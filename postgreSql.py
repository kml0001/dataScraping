import psycopg2
from psycopg2 import sql
import json

# Database connection configuration
db_params = {
    'dbname': '',
    'user': '',
    'password': '',
    'host': '',
    'port': ''
}

connection = psycopg2.connect(**db_params)
cursor = connection.cursor()

# Database table list
cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
table_names = cursor.fetchall()

output_file = 'data/database_metadata.txt'

db_dict = {}

with open(output_file, 'w') as f:
    for table_name in table_names:
        table_info = {
            'attributes': [],
            'relations': []
        }
        f.write(f"Table: {table_name[0]}\n")

        # Get table column information
        cursor.execute(sql.SQL("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s"),
                       [table_name[0]])
        columns = cursor.fetchall()

        for column in columns:
            table_info['attributes'].append((column[0], column[1]))
            f.write(f"  Column: {column[0]} - Type: {column[1]}\n")

        # Get the foreign keys of the table
        cursor.execute(sql.SQL("""
            SELECT 
                conname AS foreign_key_name,
                conrelid::regclass AS table_name,
                a.attname AS column_name,
                confrelid::regclass AS referenced_table_name,
                af.attname AS referenced_column_name
            FROM 
                pg_constraint AS c
                JOIN pg_attribute AS a ON a.attnum = ANY(c.conkey) AND a.attrelid = c.conrelid
                JOIN pg_attribute AS af ON af.attnum = ANY(c.confkey) AND af.attrelid = c.confrelid
            WHERE 
                c.contype = 'f' 
                AND c.conrelid = %s::regclass;
        """), [table_name[0]])
        foreign_keys = cursor.fetchall()

        for foreign_key in foreign_keys:
            fk_to_save = (foreign_key[2], foreign_key[3], foreign_key[4])
            from_elements = [tupla[0] for tupla in table_info['relations']]
            to_elements = [tupla[2] for tupla in table_info['relations']]
            if fk_to_save[0] not in from_elements and fk_to_save[2] not in to_elements:
                table_info['relations'].append(fk_to_save)
                f.write(
                    f"  Foreign Key: {foreign_key[0]} - Table Name: {foreign_key[1]} - Column Name: {foreign_key[2]} - "
                    f"Referenced Table Name: {foreign_key[3]} - Referenced Column Name: {foreign_key[4]}\n")

        db_dict[table_name[0]] = table_info
        f.write('\n')

cursor.close()
connection.close()

with open('data/database_metadata.json', 'w') as json_file:
    json.dump(db_dict, json_file, indent=4)

print(f"Metadatos exportados correctamente a {output_file}")

