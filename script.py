#!/usr/bin/env python

import json
import re
import sys
import fitz  # PyMuPDF
import argparse
from collections import defaultdict
import logging


logging.basicConfig(format="%(levelname)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Open the PDF file
def extract_texts_from_pdf(file_path):
    """Extracts texts from given pdf"""

    logger.info("Extracting texts from file...")
    extracted_text_lines = []

    pdf_document = fitz.open(file_path)
    # Box coordinates to be crop texts from (left, top, right, bottom)
    box_coordinates = (50, 116, 600, 812)
    # Iterate through pages from page 4 to the end.
    # Schedule of notices of leases starts from the 4th page to the last page
    for page_number in range(3, len(pdf_document)):
        page = pdf_document.load_page(page_number)
        # Crop the text within the specified box coordinates
        cropped_text = page.get_text("text", clip=box_coordinates)
        # Split the text into lines using new line delimiter
        lines = cropped_text.strip().split('\n')
        # Append each line to a list
        extracted_text_lines.append(lines)
    # Close the PDF document
    pdf_document.close()

    logger.info("Finish extracting texts from file...")
    return extracted_text_lines


def split_extracted_lines_to_list(extracted_lines):
    """Splits text in given text line by new line"""

    logger.info("Splitting extracted texts by new line...")
    # Initialize a list to store extracted text lines
    extracted_lines_list = []
    # Append each line to the list with four columns
    for lines in extracted_lines:
        for line in lines:
            # Exclude lines containing "end of register" and lines
            # with only "p"
            if "end of register" not in line.lower() and line.strip() != "p":
                # Each column is separated by at least a double spacing
                # Split each line with 2 spaces and more, to get texts
                # for each column. 
                columns = re.split(r'[ ]{2,}', line)
                # Ensure each line has exactly four columns
                # One exception of columns more than 4, due to double spacing
                # between texts
                if len(columns) > 4:
                    # Update columns values, clean up double space
                    columns[1] = f"{columns[1]} {columns[2]}"
                    columns.pop(2)
                # For lines with 2 columns after split, create empty string to
                # fill blank columns
                if len(columns) == 2:
                    if not columns[0]:
                        columns[0:0] = [""]
                    else:
                        columns[1:1] = [""]
                # Fill columns less than 4 with empty string
                while len(columns) < 4:
                    columns.append('')
                extracted_lines_list.append(columns)
    logger.info("Completed splitting extracted texts by line...")
    return extracted_lines_list


def format_schedule_entry(schedule_of_notice_lists):
    logger.info("Formatting schedule entries...")
    # list of dicts representing each entry for schedule of leases
    schedule_entry = []
    # Set default dict to save each line entry
    current_entry = defaultdict(lambda: defaultdict(dict))

    # To keep in memory when one entry has been completed
    done = False
    for idx, row in enumerate(schedule_of_notice_lists):
        # Keep entry number - represents starts of an entry
        if row[0].isdigit():
            done = False
            if current_entry["EntryNumber"]:
                # Add to schedule entry
                schedule_entry.append(current_entry)
            # Update the current entry
            # Set entry number and leases columns
            current_entry = {"EntryNumber": row[0],
                             "EntryDate": "",
                             "entryType": "Schedule of Notices of Leases",
                             "EntryText": {
                                 "Registration date and plan Ref": "",
                                 "Property description": row[1],
                                 "Date of lease and term": row[2],
                                 "Lessee's title": row[3]}
                             }

        # Store entry notes if available
        elif row[0].startswith("NOTE"):
            # Notes will ideally be in the first index of the row, however for
            # cases with double spacing, it will move to other index.
            # Hence, the join.
            # Right strip to remove empty spaces from the other indices.
            note = ' '.join(row).rstrip()
            current_entry["EntryText"]["Note"] = note
            # Checks subsequent line(s) to see if notes continue
            # Gets the next row's index
            next_row_idx = idx+1
            # If the next row is not a number(signifying start of a new entry),
            # then we keep saving the notes.
            while not schedule_of_notice_lists[next_row_idx][0].isdigit():
                # For double spacing or more cases in subsequent lines of note
                next_note = ''.join(schedule_of_notice_lists[next_row_idx])
                current_entry["EntryText"]["Note"] += f" {next_note}"
                # Increment next row index
                next_row_idx += 1
        # Update current entry with next entry line
        else:
            # Update each column for the entry
            if not done:
                # Update if next line is a digit, representing new entry
                current_entry["EntryText"]["Registration date and plan Ref"] += f" {row[0]} "
                current_entry["EntryText"]["Property description"] += f" {row[1]}"
                current_entry["EntryText"]["Date of lease and term"] += f" {row[2]}"
                current_entry["EntryText"]["Lessee's title"] += f" {row[3]}"
            # Strip extra white space from each entry
            current_entry["EntryText"] = {k: v.strip() for k, v in current_entry["EntryText"].items()}
            # Get value in next row using the row index
            if idx != len(schedule_of_notice_lists)-1:
                next_row_idx = idx+1
            else:
                next_row_idx = idx
            next_row = schedule_of_notice_lists[next_row_idx]
            # Entry is complete when the next row is blank or a note
            # Next entry usually starts with a digit - entry number
            if (next_row[0] == "" and not any(next_row)) or next_row[0].startswith("NOTE"):
                done = True

    # Append the last entry
    if current_entry["EntryNumber"]:
        schedule_entry.append(current_entry)

    logger.info("Formatting schedule entries completed...")
    return schedule_entry


def process_schedule_of_notices_of_leases(pdf_file_path):
    """Processing the extraction of schedule entry from pdf"""

    logger.info("Processing schedule of notices of leases from pdf file...")
    extracted_texts = extract_texts_from_pdf(pdf_file_path)
    # Take out only lines starting the schedule of notice of leases
    # This ensures I only start from first entry of schedule notice, 
    # ignoring every other thing on the 4th page
    schedule_of_notice_lists = split_extracted_lines_to_list(extracted_texts)[24:]
    # format schedule entries
    schedule_entry = format_schedule_entry(schedule_of_notice_lists)
    logger.info("Finished processing schedule of notices of leases...")
    return schedule_entry


def save_schedule_entry_to_json(schedule_entry, json_file_path):
    """Saves schedule entry to json file"""

    logger.info("Saving schedule of notices of leases to file...")
    output_dict = defaultdict(lambda: defaultdict(dict))
    output_dict["leaseschedule"]["scheduleType"] = "SCHEDULE OF NOTICES OF LEASE"
    output_dict["leaseschedule"]["scheduleEntry"] = schedule_entry
    # Serialize json
    json_object = json.dumps(output_dict, indent=4)

    # Writing output_dict to json file
    with open(json_file_path, "w") as outfile:
        outfile.write(json_object)
    logger.info(f"Schedule of notices of leases saved to {json_file_path}")


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(prog="Notices of lease",
                                         description="Script to get schedule"
                                         "of notice of lease from register pdf",
                                         epilog="Gets schedule of notices of lease")
    arg_parser.add_argument("-f", "--file", help="pdf file path to extract from",
                            default="register.pdf")
    arg_parser.add_argument("-o", "--output", help="json file to save result to",
                            default="output.json")
    try:
        args = arg_parser.parse_args()
        pdf_file = args.file
        output_file = args.output
        schedule_entry = process_schedule_of_notices_of_leases(pdf_file)
    except Exception as e:
        e_name = type(e).__name__
        logger.error(f"Error getting schedule of notice of leave:\n{e_name} - {e}\n")
        arg_parser.print_help(sys.stderr)
        sys.exit(1)
    save_schedule_entry_to_json(schedule_entry, output_file)
    logger.info("Done!")
