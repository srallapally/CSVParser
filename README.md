# Design Document for SOXParser.py

## Introduction

The `SOXParser.py` script is designed to process CSV files containing custom permission attributes. It identifies the structure of the CSV, processes permission data, and generates multiple output files including permission CSVs, a processed main CSV, and a Groovy schema script. This document outlines the design and development plan for these features.

## Features Overview

1. **Encoding Detection**
2. **CSV Structure Identification**
3. **Permission Data Processing**
4. **Output File Generation**
5. **Command-line Interface (CLI)**

## Detailed Design

### 1. Encoding Detection

**Function:** `detect_encoding(file_path)`

- **Purpose:** Detect the encoding of the input CSV file to ensure correct reading of file contents.
- **Library:** `chardet`
- **Input:** Path to the CSV file.
- **Output:** Encoding type as a string.
- **Development Steps:**
  1. Read the file in binary mode.
  2. Use `chardet` to detect encoding from the raw binary data.
  3. Return the detected encoding.

### 2. CSV Structure Identification

**Function:** `identify_csv_structure(input_file, permission_columns)`

- **Purpose:** Identify the CSV dialect and headers, normalize column names, and validate the presence of specified permission columns.
- **Libraries:** `csv`
- **Input:** Path to the input CSV file and a list of permission columns.
- **Output:** List of identified and normalized permission columns.
- **Development Steps:**
  1. Detect the file encoding using `detect_encoding`.
  2. Open the CSV file with the detected encoding.
  3. Use `csv.Sniffer` to determine the CSV dialect.
  4. Read the headers and normalize column names.
  5. Check if specified permission columns exist in the headers.
  6. If not all columns are found, attempt to match similar column names and warn the user.
  7. Return the list of identified permission columns.

### 3. Permission Data Processing

**Function:** `process_permissions(input_file, permission_columns)`

- **Purpose:** Extract data for permission columns and generate synthetic IDs.
- **Libraries:** `csv`
- **Input:** Path to the input CSV file and a list of permission columns.
- **Output:** Dictionary of permissions with synthetic IDs.
- **Development Steps:**
  1. Detect the file encoding using `detect_encoding`.
  2. Open the CSV file with the detected encoding.
  3. Initialize a counter for synthetic ID generation.
  4. Iterate through the rows of the CSV.
  5. For each permission column, append the permission data and synthetic ID to the dictionary.
  6. Return the dictionary of permissions.

### 4. Output File Generation

**Functions:**
- `write_permissions_csv(permissions, output_file)`
- `process_main_csv(input_file, output_file, permissions, permission_columns)`
- `generate_groovy_schema(input_file, output_file, permission_columns)`

- **Purpose:** Write processed permission data to CSV files and generate a Groovy schema script.
- **Libraries:** `csv`
- **Input:** Processed permission data, input CSV file, and permission columns.
- **Output:** Permission CSV files, processed main CSV file, and a Groovy schema script.
- **Development Steps:**
  - **write_permissions_csv:**
    1. Create and open an output CSV file for writing.
    2. Write headers and permission data to the file.
  - **process_main_csv:**
    1. Open the input CSV file and create an output CSV file.
    2. Read and process each row, integrating synthetic IDs for permission columns.
    3. Write the processed data to the output file.
  - **generate_groovy_schema:**
    1. Create and open an output file for writing the Groovy schema.
    2. Write the schema definition for each permission column.
    3. Define operation options for the schema.

### 5. Command-line Interface (CLI)

**Function:** `main(input_file, output_prefix, permission_columns)`

- **Purpose:** Provide a user interface for specifying input and output files and permission columns via command-line arguments.
- **Library:** `argparse`
- **Input:** Command-line arguments for the input file, output prefix, and permission columns.
- **Output:** Processed output files based on the provided arguments.
- **Development Steps:**
  1. Define command-line arguments using `argparse`.
  2. Parse the arguments.
  3. Call the main function with parsed arguments to initiate processing.
