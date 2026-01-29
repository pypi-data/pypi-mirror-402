import re
import os

table_name = None

with open("/Users/zsolthorvath/Downloads/gcp_trivy_scanner 2.sql", "r") as f_read:
    with open("/Users/zsolthorvath/Downloads/gcp_trivy_scanner-2-fixed.sql", "w") as f_write:
        for line in f_read:
            m = re.match('LOCK TABLES `(.*)` WRITE;', line)
            if m:
                table_name = m.group(1)
                print("Matched")
            elif line.startswith('/*!40000 ALTER TABLE `entity_meta_field` DISABLE KEYS */;'):
                print(f"{line} -> {table_name}")
                line = f"/*!40000 ALTER TABLE `{table_name}` DISABLE KEYS */;"

            f_write.write(f"{line}")