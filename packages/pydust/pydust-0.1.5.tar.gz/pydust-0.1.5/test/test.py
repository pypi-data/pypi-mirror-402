import mysql.connector
from mysql.connector import errorcode
import io
import traceback
import os
import datetime

FORMAT_DB_DATETIME = "%Y-%m-%d %H:%M:%S"

DEFAULT_MAX_PACKET_SIZE = 4 * 1024 * 1024
DEFAUTL_MAX_NUM_OF_INSERTS = 1000
DEFAULT_SPLIT_DUMP_FILES = True

def _create_connection():
    conn = None
    try:
        conn = mysql.connector.connect(user=MYSQL_USER, password=MYSQL_PASSWORD, host=MYSQL_HOST, database=MYSQL_DB, charset='utf8', use_unicode=True)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

    return conn

def _close_connection(conn):
    if conn:
        conn.commit()
        conn.close()

def _create_cursor(conn, prepared=False, buffered=True):
    if conn:
        return conn.cursor(buffered=buffered, prepared=prepared)

def _close_cursor(c):
    if c:
        c.close()

def _start_dump_file(stream, file_counter):
    stream.write(f"-- MySQL dump (pydust), file_counter: {file_counter}\n"+
                    "--\n"+
                    f"-- Host: {os.environ.get('HOSTNAME')}    Database: {MYSQL_DB}\n"+
                    "-- ------------------------------------------------------\n"+
                    f"-- Server version	{mysql_version}\n\n")

    stream.write("/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;\n"+
                    "/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;\n"+
                    "/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;\n"+
                    "/*!50503 SET NAMES utf8mb4 */;\n"+
                    "/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;\n"+
                    "/*!40103 SET TIME_ZONE='+00:00' */;\n"+
                    "/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;\n"+
                    "/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;\n"+
                    "/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;\n"+
                    "/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;\n\n")

def _end_dump_file(stream):
    stream.write("/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;\n"+
                    "/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;\n"+
                    "/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;\n"+
                    "/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;\n"+
                    "/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;\n"+
                    "/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;\n"+
                    "/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;\n\n"+
                    f"-- Dump completed on {datetime.datetime.strftime(datetime.datetime.now(), FORMAT_DB_DATETIME)}\n")

conn = _create_connection()

try:
    file_counter = 0

    c = _create_cursor(conn, buffered=False)

    max_packet_size = int(os.environ.get("MYSQL_MAX_ALLOWED_PACKET_SIZE", DEFAULT_MAX_PACKET_SIZE))
    max_num_of_inserts = int(os.environ.get("MYSQL_MAX_NUM_OF_INSERTS", DEFAUTL_MAX_NUM_OF_INSERTS))
    split_files = bool(os.environ.get("MYSQL_SPLIT_DUMP_FILES", DEFAULT_SPLIT_DUMP_FILES))
    
    mysql_version = ""

    c.execute("SHOW VARIABLES LIKE 'version'")
    for vars in c.fetchall():
        mysql_version = vars[1]

    c.execute("SHOW TABLES")
    tables = []
    for table in c.fetchall():
        tables.append(table[0])

    # Lower the packet size slightly
    max_packet_size -= 1000

    for table in tables:
        stream = open("gcp_trivy_scanner_{}.sql".format(str(file_counter).zfill(6)), "w")
        _start_dump_file(stream, file_counter)
    
        stream.write("--\n"+
                    f"-- Table structure for table `{table}`\n"+
                    "--\n\n")
        stream.write("DROP TABLE IF EXISTS `" + str(table) + "`;\n")

        stream.write("/*!40101 SET @saved_cs_client     = @@character_set_client */;\n"+
                    "/*!50503 SET character_set_client = utf8mb4 */;")

        c.execute("SHOW CREATE TABLE `" + str(table) + "`;")
        stream.write("\n" + str(c.fetchone()[1]) + ";\n");

        stream.write("/*!40101 SET character_set_client = @saved_cs_client */;\n\n")

        stream.write("--\n"+
                    f"-- Dumping data for table `{table}`\n"+
                    "--\n\n"+
                    f"LOCK TABLES `{table}` WRITE;\n"+
                    f"/*!40000 ALTER TABLE `{table}` DISABLE KEYS */;\n")

        # Get fields:
        c.execute("DESCRIBE `" + str(table) + "`;")
        fields = []
        for field in c.fetchall():
            field_type = field[1]
            if field_type.lower() in ["binary", "varbinary", "blob", "mediumblob", "longblob"]:
                fields.append((f"HEX({field[0]})", field[0], True)) 
            else:
                fields.append((field[0], field[0], False)) 


        c.execute("SELECT {} FROM `{}`;".format(",".join(f[0] for f in fields), table))
        row = c.fetchone()

        row_counter = 0
        packet_length  = 0

        empty_table = True

        if row is not None:
            empty_table = False
            insert_str = "INSERT INTO `{}` ({}) VALUES ".format(table, ",".join(f[1] for f in fields))
            packet_length = len(insert_str)
            stream.write(insert_str)
            first_row = True

        while row is not None:
            row_stream = io.StringIO("")

            if not first_row:
                row_stream.write(",")

            row_stream.write("(")
            first = True
            for field_idx in range(len(fields)):
                field = fields[field_idx]
                if not first:
                    row_stream.write(",");
                if row[field_idx] is None:
                    row_stream.write("NULL")
                elif field[2]:
                    row_stream.write(f"UNHEX(\"{row[field_idx]}\")")
                elif isinstance(row[field_idx], str):
                    escaped_value = row[field_idx].replace('\\','\\\\').replace('"','\\"')
                    row_stream.write(f"\"{escaped_value}\"")
                else:
                    row_stream.write(f"\"{row[field_idx]}\"")
                first = False
            row_stream.write(")")

            row_str = row_stream.getvalue()
            if packet_length + len(row_str) > max_packet_size or ( max_num_of_inserts > 0 and row_counter > max_num_of_inserts ):
                row_counter = 0
                stream.write(";\n")

                if split_files:
                    _end_dump_file(stream)
                    stream.close()
                    file_counter += 1
                    stream = open("gcp_trivy_scanner_{}.sql".format(str(file_counter).zfill(6)), "w")
                    _start_dump_file(stream, file_counter)

                insert_str = "INSERT INTO `{}` ({}) VALUES ".format(table, ",".join(f[1] for f in fields))
                packet_length = len(insert_str)
                stream.write(insert_str)
                if not first_row:
                    row_str = row_str[1:]
            
            stream.write(row_str)
            packet_length += len(row_str)
            first_row = False

            row = c.fetchone()
            row_counter += 1

        if not empty_table:
            stream.write(";\n")

        stream.write(f"/*!40000 ALTER TABLE `{table}` ENABLE KEYS */;\n"+
                    "UNLOCK TABLES;\n\n")
        
        _end_dump_file(stream)
        stream.close()

    _close_cursor(c)

except:
    traceback.print_exc()
finally:
    _close_connection(conn)