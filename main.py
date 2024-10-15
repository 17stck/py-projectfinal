import sqlite3
import struct
import pandas as pd

# เชื่อมต่อกับฐานข้อมูล SQLite
conn = sqlite3.connect('student.db')
cursor = conn.cursor()

# สร้างตารางถ้ายังไม่มี
cursor.execute('''
CREATE TABLE IF NOT EXISTS students (
    std_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    sec INTEGER NOT NULL,
    time TEXT NOT NULL,
    checked INTEGER NOT NULL,
    cause TEXT
)
''')
conn.commit()

# ฟังก์ชันบันทึกข้อมูลในไฟล์ .txt


def log_to_file(action, data):
    with open('student_log.txt', 'a', encoding='utf-8') as f:
        f.write(f"{action}: {data}\n")
        f.close()

# ฟังก์ชันบันทึกข้อมูลในไฟล์ไบนารี


def save_to_binary_file(data):
    with open('student_data.bin', 'ab') as f:
        # ตัด string ที่ยาวเกินขนาดที่กำหนด และแปลง string เป็น bytes ถ้าจำเป็น
        name = data[1][:50] if isinstance(
            data[1], bytes) else data[1][:50].encode('utf-8')
        sec = data[2][:10] if isinstance(
            data[2], bytes) else data[2][:10].encode('utf-8')
        time = data[3][:8] if isinstance(
            data[3], bytes) else data[3][:8].encode('utf-8')
        cause = data[5][:50] if isinstance(
            data[5], bytes) else data[5][:50].encode('utf-8')

        # เติม string ที่ไม่เต็มขนาดด้วย null bytes (b'\0') เพื่อให้ตรงกับรูปแบบที่กำหนด
        name = name.ljust(50, b'\0')
        sec = sec.ljust(10, b'\0')
        time = time.ljust(8, b'\0')
        cause = cause.ljust(50, b'\0')

        # บรรจุข้อมูลลงใน struct (Q50s10s8si50s)
        binary_data = struct.pack(
            'Q50s10s8si50s', data[0], name, sec, time, data[4], cause)
        f.write(binary_data)
        f.close()

# เมนูการใช้งาน


def menu():
    print("\n" + "*" * 30)
    print("*" + " ""Student Management Check""  ""*")
    print("*" * 30)
    print("* 1. Add student             *")
    print("* 2. Edit student            *")
    print("* 3. Delete student          *")
    print("* 4. Search student          *")
    print("* 5. Export binary data      *")
    print("* 6. List students           *")
    print("* 7. Generate report         *")
    print("* 8. Exit                    *")
    print("*" * 30)

# เพิ่มนักเรียน


def add_student():
    try:
        std_id = int(input("Enter Student ID: "))
        name = input("Enter Name: ")
        sec = input("Enter Section: ")
        time = input("Enter Time (format HH:MM): ")
        checked = int(input("Enter checked (0 or 1): "))
        cause = input("Enter Cause: ")

        cursor.execute("INSERT INTO students (std_id, name, sec, time, checked, cause) VALUES (?, ?, ?, ?, ?, ?)",
                       (std_id, name, sec, time, checked, cause))
        conn.commit()
        log_to_file(
            "Add", f"ID: {std_id}, Name: {name} , Section: {sec}, Time: {time}, checked: {checked}, Cause: {cause}")
        print("Student added successfully.")
    except sqlite3.IntegrityError:
        print("Error: This student ID already exists.")
    except ValueError:
        print("Error: Invalid input type. Please enter the correct type of data.")
    except Exception as e:
        print(f"An error occurred: {e}")


# แก้ไขนักเรียน
def edit_student():
    try:
        std_id = int(input("Enter Student ID to Edit: "))
        # ตรวจสอบว่ามี student ID ในฐานข้อมูลหรือไม่
        cursor.execute("SELECT * FROM students WHERE std_id = ?", (std_id,))
        student = cursor.fetchone()
        if student is None:
            print(
                f"Error: Student ID {std_id} does not exist. Please try again.")
            return
        # ข้อมูลเดิมที่อยู่ในฐานข้อมูล
        current_name, current_sec, current_time, current_checked, current_cause = student[
            1:6]
        # รับข้อมูลใหม่จากผู้ใช้ (ถ้าไม่กรอกจะใช้ข้อมูลเดิม)
        name = input(
            f"Enter New Name (Current: {current_name}): ") or current_name
        sec = input(
            f"Enter New Section (Current: {current_sec}): ") or current_sec
        time = input(
            f"Enter New Time (format HH:MM, Current: {current_time}): ") or current_time

        # ตรวจสอบค่าที่ใส่เข้าไปในช่อง checked ถ้าเคาะผ่านจะใช้ค่าเดิม
        checked_input = input(
            f"Enter New Checked (0 or 1, Current: {current_checked}): ")
        if checked_input == "":
            checked = current_checked  # ใช้ค่าเดิมถ้าไม่ได้ใส่ข้อมูลใหม่
        else:
            checked = int(checked_input)  # แปลงค่าที่ใส่เป็น int

        cause = input(
            f"Enter New Cause (Current: {current_cause}): ") or current_cause
        # อัปเดตข้อมูลในฐานข้อมูล
        cursor.execute(
            "UPDATE students SET name = ?, sec = ?, time = ?, checked = ?, cause = ? WHERE std_id = ?",
            (name, sec, time, checked, cause, std_id))
        conn.commit()
        # บันทึกการเปลี่ยนแปลงลงใน log
        log_to_file(
            "Edit", f"ID: {std_id}, Name: {name}, Section: {sec}, Time: {time}, Checked: {checked}, Cause: {cause}")
        print("Student updated successfully.")
    except sqlite3.IntegrityError:
        print("Error: This student ID does not exist.")
    except ValueError:
        print("Error: Invalid input type. Please enter the correct type of data.")
    except Exception as e:
        print(f"An error occurred: {e}")

# ลบนักเรียน


def delete_student():
    try:
        std_id = int(input("Enter Student ID to Delete: "))
        cursor.execute("DELETE FROM students WHERE std_id = ?", (std_id,))
        if cursor.rowcount == 0:
            print("Error: No student found with the given ID.")
        else:
            conn.commit()
            log_to_file("Delete", f"ID: {std_id}")
            print("Student deleted successfully.")
    except ValueError:
        print("Error: Invalid input. Please enter a valid Student ID.")
    except Exception as e:
        print(f"An error occurred: {e}")

# ค้นหานักเรียนโดยระบุ ID


def search_student():
    try:
        std_id = int(input("Enter Student ID to Search: "))
        cursor.execute("SELECT * FROM students WHERE std_id = ?", (std_id,))
        student = cursor.fetchone()
        if student:
            print(
                f"ID: {student[0]}, Name: {student[1]}, Section: {student[2]}, Time: {student[3]}, checked: {student[4]}, Cause: {student[5]}")
            log_to_file("Search", f"ID: {std_id}")
        else:
            print("Student not found.")
    except ValueError:
        print("Error: Invalid input. Please enter a valid Student ID.")
    except Exception as e:
        print(f"An error occurred: {e}")

# export binary data to txt


def export_binary_data():
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    if students:
        for student in students:
            name = student[1].encode('utf-8')[:50]
            sec = sec = str(student[2]).encode('utf-8')[:10]
            time = student[3].encode('utf-8')[:8]
            cause = student[5].encode('utf-8')[:50]
            data = (student[0], name, sec, time, student[4], cause)
            save_to_binary_file(data)
        print("Data exported to binary file successfully.")
    else:
        print("No students found.")


# ฟังก์ชันแสดงรายงานนักเรียนในรูปแบบตารางในไฟล์ .txt
def report_students_to_txt(filename='students_report.txt'):
    cursor.execute("SELECT * FROM students ORDER BY std_id")
    students = cursor.fetchall()

    with open(filename, 'w', encoding='utf-8') as file:
        if students:
            # ส่วนหัวของตาราง
            file.write("=" * 90 + "\n")
            file.write(
                f"{'No':<10}{'Name':<23}{'Section':<15}{'Time':<12}{'Checked':<12}{'Cause':<20}\n")
            file.write("=" * 90 + "\n")

            on_time_students = []
            late_students = []
            absent_students = []

            for student in students:
                time = student[3]
                checked = student[4]

                if checked == 0:
                    absent_students.append(student)
                elif time <= "08:29":
                    on_time_students.append(student)
                else:
                    late_students.append(student)

            # แสดงข้อมูลนักเรียนที่มาตรงเวลา
            if on_time_students:
                for idx, student in enumerate(on_time_students, start=1):
                    file.write(
                        f"{idx:<10}{student[1]:<25}{student[2]:<13}{student[3]:<14}{student[4]:<11}{student[5]:<20}\n")

                file.write(
                    f"Total students on time: {len(on_time_students)}\n")
            else:
                file.write("No students on time.\n")

            # แสดงข้อมูลนักเรียนที่มาสาย
            file.write("-" * 90 + "\n")
            if late_students:
                for idx, student in enumerate(late_students, start=1):
                    file.write(
                        f"{idx:<10}{student[1]:<25}{student[2]:<13}{student[3]:<14}{student[4]:<11}{student[5]:<20}\n")

                file.write(f"Total late students: {len(late_students)}\n")
            else:
                file.write("No late students.\n")

            # แสดงข้อมูลนักเรียนที่ขาด
            file.write("-" * 90 + "\n")
            if absent_students:
                for idx, student in enumerate(absent_students, start=1):
                    file.write(
                        f"{idx:<10}{student[1]:<25}{student[2]:<13}{student[3]:<14}{student[4]:<11}{student[5]:<20}\n")

                file.write(f"Total absent students: {len(absent_students)}\n")
            else:
                file.write("No absent students.\n")

            # สรุปจำนวน
            file.write("=" * 90 + "\n")
            file.write(f"Total number of students: {len(students)}\n")
            print("Report created successfully.")
        else:
            file.write("No students found.\n")

        file.close()


# ฟังก์ชันแสดงรายชื่อนักเรียนทั้งหมดเรียงตาม std_id
def list_students():
    cursor.execute("SELECT * FROM students ORDER BY std_id")
    students = cursor.fetchall()

    if students:
        # จัด format header และข้อมูลสำหรับการแสดงใน console
        print("=" * 88)
        print(
            f"{'ID':<22}{'Name':<19}{'Section':<15}{'Time':<12}{'Checked':<12}{'Cause':<20}")
        print("=" * 88)

        for student in students:
            print(
                f"{student[0]:<22}{student[1]:<20}{student[2]:<15}{student[3]:<12}{student[4]:<12}{student[5]:<20}")

        print("=" * 88)
        print(f"Total number of students: {len(students)}")
        print("List of students update successfully.")
    else:
        print("No students found.")


# เริ่มต้นเมนูหลัก
while True:
    menu()
    try:
        choice = int(input("Select an option: "))

        if choice == 1:
            add_student()
        elif choice == 2:
            edit_student()
        elif choice == 3:
            delete_student()
        elif choice == 4:
            search_student()
        elif choice == 5:
            export_binary_data()
        elif choice == 6:
            list_students()  # เรียกใช้ฟังก์ชันแสดงรายชื่อ
        elif choice == 7:
            report_students_to_txt()  # เรียกใช้ฟังก์ชันสร้างรายงาน
        elif choice == 8:
            confirm_exit = input(
                "Are you sure you want to exit? (y/n): ").lower()
            if confirm_exit == 'y':
                print("Exiting program.")
                break
            else:
                print("Continuing program.")
        else:
            print("Invalid option. Please try again.")
    except ValueError:
        print("Invalid input. Please enter a number.")

conn.close()
