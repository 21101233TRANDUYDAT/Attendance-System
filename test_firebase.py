from firebase.firebase_service import FirebaseService
from datetime import datetime

if __name__ == "__main__":
    firebase = FirebaseService()

    #add new employee
    # firebase.add_employee(
    #     employee_id="21101711",
    #     name="CAO THUY PHUONG",
    #     major="Marketing",
    #     age= 24,
    #     email="caophuong@gmail.com",
    #     phone_number="0355381111",
    #     password= "251100",
    #     role= "user"
    # )

    # #update employee information
    employee_id = "21101711"
    # updates = {
    #     "check_in_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    #     "attendance": 10,
    #     "late": 3,
    #     "check_out_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # }
    # firebase.update_employee(employee_id, updates)
    #
    # #get information
    # employee_data = firebase.get_employee(employee_id)
    # if employee_data:
    #     print("Employee Data:")
    #     for key, value in employee_data.items():
    #         print(f"{key}:{value}")
    # else:
    #     print("Employee not found.")

    # # get information with field
    # employee_name = firebase.get_employee(employee_id,field="name")
    # employee_major = firebase.get_employee(employee_id, field="major")
    # employee_age = firebase.get_employee(employee_id, field="age")
    # print("employee name: ", employee_name)
    # print("employee major: ", employee_major)
    # print("employee age: ", employee_age)
    # check_in_time = firebase.get_employee(employee_id,field="check_in_time")
    # print(check_in_time)
    # last_check_in_date = datetime.strptime(check_in_time, '%Y-%m-%d %H:%M:%S').date()
    # print(last_check_in_date)
    #
    # #log access update:
    # firebase.log_access(
    #     employee_id=employee_id,
    #     status="check-out",
    #     timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # )
    # #get access_logs
    # access_logs = firebase.get_access_logs(employee_id)
    #
    # if access_logs:
    #     print(f"Access logs for employee {employee_id}:")
    #     for log_id, log_data in access_logs.items():
    #         print(f"Log ID: {log_id}")
    #         print(f"Status: {log_data['status']}")
    #         print(f"Timestamp: {log_data['timestamp']}")
    # else:
    #     print("No access logs available.")
    #
    # #get all employees
    #
    # all_employees = firebase.get_all_employee()
    #
    # if all_employees:
    #     print("All employee:")
    #     for employee_id, employee_data in all_employees.items():
    #         print(f"Employee ID: {employee_id}")
    #         for key, value in employee_data.items():
    #             print(f"{key}:{value}")
    # else:
    #     print("No employee found.")

    #get all employees with filter
    # filtered_employees = firebase.get_all_employee(filter_by={'major':'Computer Science', "late": lambda x: x >= 2})
    #
    # if filtered_employees:
    #     print("Filtered Employees:")
    #     for emp_id, data in filtered_employees.items():
    #         print(f"Employee ID: {emp_id}")
    #         for key, value in data.items():
    #             print(f"{key}:{value}")
    # else:
    #     print("No employees match the filter.")

    #update attendance
    # firebase.update_attendance(employee_id)

