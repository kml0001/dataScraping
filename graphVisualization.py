from graphviz import Digraph
import json

with open('data/database_metadata.json', 'r') as json_file:
    data = json.load(json_file)

dot = Digraph(format='png', node_attr={'shape': 'record'})

# Add nodes and relations
for table, info in data.items():
    node_label = f"{{ {table} | "

    for attribute_info in info['attributes']:
        attribute_name, data_type = attribute_info
        attribute_label = f"<{attribute_name}>{attribute_name}: {data_type}"
        node_label += attribute_label + " | "

    node_label += "}"
    dot.node(table, label=node_label)

    ## DEBUG OPTION
    # for relation in info['relations']:
    #     from_attribute, to_table, to_column = relation
    #     edge_label = f"{from_attribute} -> {to_column}"
    #     dot.edge(table, to_table, label=edge_label)

    for relation in info['relations']:
        from_attribute, to_table, to_column = relation
        dot.edge(f"{table}:{from_attribute}", f"{to_table}:<{to_column}>")

dot.render('data/ERD', view=True)
