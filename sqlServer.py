import pyodbc
import json

# Database connection configuration for SQL Server with Windows Authentication
db_params = {
    'server': '',  # The name or IP address of the SQL Server instance
    'database': '',  # The name of the database you want to connect to
    'trusted_connection': 'yes',  # Indicates Windows Authentication
    'driver': 'ODBC Driver 17 for SQL Server'
}

# Establish a connection to SQL Server
connection = pyodbc.connect(**db_params)
cursor = connection.cursor()

# Database table list
cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'dbo'")
table_names = cursor.fetchall()

output_file = 'data/database_sqlserver.txt'

db_dict = {}

with open(output_file, 'w') as f:
    for table_name in table_names:
        table_info = {
            'attributes': [],
            'relations': []
        }
        f.write(f"Table: {table_name[0]}\n")

        # Get table column information
        cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name[0]}'")
        columns = cursor.fetchall()

        for column in columns:
            table_info['attributes'].append((column.column_name, column.data_type))
            f.write(f"  Column: {column.column_name} - Type: {column.data_type}\n")

        # Get the foreign keys of the table
        cursor.execute("""
            SELECT 
                C.CONSTRAINT_NAME AS foreign_key_name,
                T.TABLE_NAME AS table_name,
                K.COLUMN_NAME AS column_name,
                FK.TABLE_NAME AS referenced_table_name,
                KF.COLUMN_NAME AS referenced_column_name
            FROM 
                INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS C
                INNER JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS FK ON C.UNIQUE_CONSTRAINT_NAME = FK.CONSTRAINT_NAME
                INNER JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS T ON C.CONSTRAINT_NAME = T.CONSTRAINT_NAME
                INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE K ON C.CONSTRAINT_NAME = K.CONSTRAINT_NAME
                INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE KF ON FK.CONSTRAINT_NAME = KF.CONSTRAINT_NAME
            WHERE 
                T.TABLE_NAME = ?
        """, [table_name[0]])
        foreign_keys = cursor.fetchall()

        for foreign_key in foreign_keys:
            fk_to_save = (foreign_key.column_name, foreign_key.referenced_table_name, foreign_key.referenced_column_name)
            from_elements = [tupla[0] for tupla in table_info['relations']]
            to_elements = [tupla[2] for tupla in table_info['relations']]
            if fk_to_save[0] not in from_elements and fk_to_save[2] not in to_elements:
                table_info['relations'].append(fk_to_save)
                f.write(
                    f"  Foreign Key: {foreign_key.foreign_key_name} - Table Name: {foreign_key.table_name} - "
                    f"Column Name: {foreign_key.column_name} - "
                    f"Referenced Table Name: {foreign_key.referenced_table_name} - "
                    f"Referenced Column Name: {foreign_key.referenced_column_name}\n")

        db_dict[table_name[0]] = table_info
        f.write('\n')

cursor.close()
connection.close()

with open('data/database_metadata.json', 'w') as json_file:
    json.dump(db_dict, json_file, indent=4)

print(f"Metadata exported successfully to {output_file}")
