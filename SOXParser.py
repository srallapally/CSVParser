import csv
import sys
import os
import chardet
import argparse


def generate_synthetic_id(counter):
    return f"{counter:04d}"


def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    return chardet.detect(raw_data)['encoding']


def normalize_column_name(column_name):
    return column_name.replace(' ', '_')


def identify_csv_structure(input_file, permission_columns):
    encoding = detect_encoding(input_file)
    with open(input_file, 'r', encoding=encoding) as f:
        # Try to detect the dialect
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        reader = csv.reader(f, dialect=dialect)
        headers = [normalize_column_name(header) for header in next(reader)]

        # Normalize permission column names
        normalized_permission_columns = [normalize_column_name(col) for col in permission_columns]

        # Check if all specified permission columns exist in the CSV
        if all(col in headers for col in normalized_permission_columns):
            return normalized_permission_columns
        else:
            # If not all columns are found, try to find similar column names
            found_columns = []
            for col in normalized_permission_columns:
                similar_columns = [header for header in headers if col.lower() in header.lower()]
                if similar_columns:
                    found_columns.append(similar_columns[0])
                else:
                    print(f"Warning: Could not find a column similar to '{col}'")

            if found_columns:
                print(f"Using the following columns as permission attributes: {found_columns}")
                return found_columns
            else:
                raise ValueError("Could not identify the specified permission columns in the CSV")


def process_permissions(input_file, permission_columns):
    encoding = detect_encoding(input_file)
    permissions = {col: {} for col in permission_columns}
    counters = {col: 1 for col in permission_columns}
    with open(input_file, 'r', encoding=encoding) as f:
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        reader = csv.DictReader(f, dialect=dialect)
        normalized_fieldnames = [normalize_column_name(field) for field in reader.fieldnames]
        for row in reader:
            normalized_row = {normalize_column_name(k): v for k, v in row.items()}
            for col in permission_columns:
                # Handle different separators for multiple values
                separators = [';', ',', '|']
                for separator in separators:
                    if separator in normalized_row[col]:
                        values = [v.strip() for v in normalized_row[col].split(separator) if v.strip()]
                        break
                else:
                    values = [normalized_row[col].strip()] if normalized_row[col].strip() else []

                for value in values:
                    if value not in permissions[col]:
                        permissions[col][value] = generate_synthetic_id(counters[col])
                        counters[col] += 1
    return permissions


def write_permissions_csv(permissions, output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow([f"{normalize_column_name(output_file.split('_')[-1][:-4])}_id",
                         normalize_column_name(output_file.split('_')[-1][:-4])])
        for perm, id in permissions.items():
            writer.writerow([id, perm])


def process_main_csv(input_file, output_file, permissions, permission_columns):
    encoding = detect_encoding(input_file)
    with open(input_file, 'r', encoding=encoding) as infile, open(output_file, 'w', newline='',
                                                                  encoding='utf-8') as outfile:
        dialect = csv.Sniffer().sniff(infile.read(1024))
        infile.seek(0)
        reader = csv.DictReader(infile, dialect=dialect)
        fieldnames = [normalize_column_name(field) for field in reader.fieldnames]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()

        for row in reader:
            normalized_row = {normalize_column_name(k): v for k, v in row.items()}
            for col in permission_columns:
                # Handle different separators for multiple values
                separators = [';', ',', '|']
                for separator in separators:
                    if separator in normalized_row[col]:
                        values = [v.strip() for v in normalized_row[col].split(separator) if v.strip()]
                        break
                else:
                    values = [normalized_row[col].strip()] if normalized_row[col].strip() else []

                if values:
                    normalized_row[col] = ';'.join([permissions[col].get(v, 'NULL') for v in values])
                else:
                    normalized_row[col] = 'NULL'

            writer.writerow(normalized_row)


def generate_groovy_schema(input_file, output_file, permission_columns):
    encoding = detect_encoding(input_file)
    with open(input_file, 'r', encoding=encoding) as f:
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        reader = csv.reader(f, dialect=dialect)
        headers = [normalize_column_name(header) for header in next(reader)]

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('''import org.forgerock.openicf.connectors.groovy.OperationType
import org.forgerock.openicf.connectors.groovy.ScriptedConfiguration
import org.identityconnectors.common.logging.Log
import org.identityconnectors.framework.common.objects.AttributeInfo
import org.identityconnectors.framework.common.objects.ObjectClass
import org.identityconnectors.framework.common.objects.OperationOptionInfoBuilder
import org.identityconnectors.framework.spi.operations.SearchOp

def operation = operation as OperationType
def configuration = configuration as ScriptedConfiguration
def log = log as Log

return builder.schema {
    objectClass {
        type "__ACCOUNT__"
        attributes {
''')
        for header in headers:
            attr_type = 'String.class'
            flags = []
            if header in permission_columns:
                flags.append('MULTIVALUED')

            f.write(f'            "{header}" {attr_type}')
            if flags:
                f.write(", " + ", ".join(flags))
            f.write("\n")

        f.write('''        }
    }
''')

        for perm_col in permission_columns:
            object_class_name = perm_col.upper()
            f.write(f'''
    objectClass {{
        type "{object_class_name}"
        attributes {{
            "{perm_col}_id" String.class, REQUIRED
            "{perm_col}" String.class, REQUIRED
        }}
    }}
''')

        f.write('''
    // Operation options
    defineOperationOption OperationOptionInfoBuilder.buildPagedResultsCookie(), SearchOp
    defineOperationOption OperationOptionInfoBuilder.buildPagedResultsOffset(), SearchOp
    defineOperationOption OperationOptionInfoBuilder.buildPageSize(), SearchOp
    defineOperationOption OperationOptionInfoBuilder.buildSortKeys(), SearchOp
    defineOperationOption OperationOptionInfoBuilder.buildRunWithUser()
    defineOperationOption OperationOptionInfoBuilder.buildRunWithPassword()
}
''')


def main(input_file, output_prefix, permission_columns):
    identified_columns = identify_csv_structure(input_file, permission_columns)
    print(f"Using permission columns: {identified_columns}")

    permissions = process_permissions(input_file, identified_columns)

    for col, perm_dict in permissions.items():
        write_permissions_csv(perm_dict, f"{output_prefix}_{normalize_column_name(col)}.csv")

    process_main_csv(input_file, f"{output_prefix}_main.csv", permissions, identified_columns)
    generate_groovy_schema(input_file, f"{output_prefix}_schema.groovy", identified_columns)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process CSV file with custom permission attributes.')
    parser.add_argument('input_file', help='Input CSV file')
    parser.add_argument('output_prefix', help='Prefix for output files')
    parser.add_argument('permission_columns', nargs='+', help='Names of the columns representing permissions')

    args = parser.parse_args()

    main(args.input_file, args.output_prefix, args.permission_columns)
    print(f"Processing complete. Output files generated with prefix: {args.output_prefix}")