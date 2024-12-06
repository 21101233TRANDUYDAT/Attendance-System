from datetime import datetime, timedelta
from utils.config import load_config
import firebase_admin
from firebase_admin import credentials, db, auth
import cloudinary
import cloudinary.uploader
import os


class FirebaseService:
    def __init__(self, config_path="config.yaml"):
        """
        init Firebase with parameter from file config.yaml.
        """
        # load config file
        self.configs = load_config(config_path)

        #firebase
        cred = credentials.Certificate(self.configs["firebase"]["credential_file"])
        firebase_admin.initialize_app(cred, {
            'databaseURL': self.configs["firebase"]["database_url"]
        })

        #Cloudinary
        cloudinary.config(
            cloud_name=self.configs["cloudinary"]["cloud_name"],
            api_key=self.configs["cloudinary"]["api_key"],
            api_secret=self.configs["cloudinary"]["api_secret"]
        )

        self.cloud_folder = self.configs["cloudinary"]["folder"]
        #load time parameters
        self.load_time_parameters()

    def load_time_parameters(self):
        time_configs = self.configs["time"]
        self.condition_time = datetime.strptime(time_configs["condition_time"], "%H:%M:%S").time()
        self.check_out_time = datetime.strptime(time_configs["check_out_time"], "%H:%M:%S").time()

    def add_employee(self, employee_id, name, major, age, email, phone_number, role, password):
        """
        add new employee
        """
        # make account in Firebase Authentication
        user = auth.create_user(
            email=email,
            password=password,
            display_name=name
        )
        uid = user.uid  # UID

        ref = db.reference(f'Employee/{employee_id}')
        ref.set({
            "name": name,
            "major": major,
            "age": age,
            "email": email,
            "phone_number": phone_number,
            "password": password,
            "uid": uid,
            "attendance": 0,
            "late": 0,
            "check_in_time": None,
            "check_out_time": None,
            "photo_url": None,
            "role": role
        })
        print(f"Employee {name} added successfully!")

    def update_employee(self, employee_id, updates):
        """

        """
        ref = db.reference(f'Employee/{employee_id}')
        ref.update(updates)
        print(f"Updated employee {employee_id} successfully!")

    def get_employee(self, employee_id, field=None):
        """
        :param employee_id:
        :param field:(str) name, major, age, phone_number...
        :return:
        """
        try:
            ref = db.reference(f'Employee/{employee_id}')
            employee_data = ref.get()

            if field:
                return employee_data.get(field, None) if employee_data else "Unknown"
            return employee_data
        except Exception as e:
            print(f"Error getting employee {employee_id}: {e}")


    def log_access(self, employee_id, status, timestamp):
        """
        write log access
        """
        ref = db.reference(f'AccessLogs/{employee_id}')

        # get current log
        last_log = ref.order_by_key().limit_to_last(1).get()
        if last_log:
            last_log_data = list(last_log.values())[0]
            last_timestamp = datetime.strptime(last_log_data.get("timestamp"), "%Y-%m-%d %H:%M:%S")
            current_timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

            # check condition
            if current_timestamp - last_timestamp < timedelta(minutes=1):
                print("Log skipped due to time threshold.")
                return

        ref.push({
            "status": status,
            "timestamp": timestamp
        })
        print(f"Access log for {employee_id} created successfully!")

    def get_access_logs(self, employee_id):
        """

        :param employee_id:
        :return:
        """
        ref = db.reference(f'AccessLogs/{employee_id}')
        access_logs = ref.get()

        if not access_logs:
            print(f"No access logs found for employee ID: {employee_id}")
            return None
        return access_logs

    def get_all_employee(self, filter_by=None):
        """

        :param filter_by:(dict) {'major': 'marketing', 'age': 20, 'attendance' : 10....}
        :return:
        """
        ref = db.reference('Employee')
        all_employees = ref.get()

        if not all_employees:
            print("No employees found in the database.")
            return None

        if filter_by:
            filtered_employee = {
                emp_id: data for emp_id, data in all_employees.items()
                if all(key in data and (data[key] == value if not callable(value) else value(data[key]))
                       for key, value in filter_by.items())
            }
            return filtered_employee

        return all_employees

    def log_alert_access(self, alert_image_url, message="Invalid Access"):
        """

        """
        try:
            # make key
            alert_id = db.reference('AlertAccess').push().key

            # Dữ liệu log
            log_data = {
                "alertImage": alert_image_url,
                "message": message,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # write alert log in Firebase
            db.reference(f'AlertAccess/{alert_id}').set(log_data)
            print(f"Log alert successfully!: {alert_id}")
        except Exception as e:
            print(f"Error when write log alert: {e}")

    def update_attendance(self, employee_id):
        """

        :param employee_id: (str)
        :return:
        """
        try:
            current_time = datetime.now()
            today_date = current_time.date()

            #get employee data
            employee_data = self.get_employee(employee_id)
            if not employee_data:
                print(f"Employee {employee_id} not found!")
                return "unknown"

            #check-in and check-out
            if self.check_in_condition(employee_data, today_date):
                return self.handle_check_in(employee_id, employee_data, current_time)


            if self.check_out_condition(employee_data, today_date, current_time):
                return self.handle_check_out(employee_id, employee_data, current_time)


            print("Already Checked today!")
            self.log_access(employee_id,"Already Checked", current_time.strftime('%Y-%m-%d %H:%M:%S'))
            return "already_checked"
            #update log access
        except Exception as e:
            print(f"Error updating attendance for employee {employee_id}: {e}")
            return "Unknown"

    #================helper methods=================
    def check_in_condition(self, employee_data, today_date):
        """

        """
        last_check_in_time = employee_data.get("check_in_time")
        last_check_in_date = datetime.strptime(last_check_in_time,'%Y-%m-%d %H:%M:%S').date() if last_check_in_time else None
        return not last_check_in_time or last_check_in_date != today_date
    #
    def check_out_condition(self, employee_data, today_date, current_time):
        """

        """
        last_check_out_time = employee_data.get("check_out_time")
        last_check_out_date = datetime.strptime(last_check_out_time,'%Y-%m-%d %H:%M:%S').date() if last_check_out_time else None
        return (not last_check_out_time or last_check_out_date != today_date) and current_time.time() > self.check_out_time

    def handle_check_in(self, employee_id, employee_data, current_time):
        """

        """
        updates = {
            "check_in_time": current_time.strftime('%Y-%m-%d %H:%M:%S'),
            "attendance": employee_data.get("attendance", 0) + 1
        }
        if current_time.time() > self.condition_time:
            updates["late"] = employee_data.get("late", 0) + 1
            log_status = "Checked In (Late)"
            status = "late"
            print("You are late!")
        else:
            log_status = "Checked In"
            status = "success"

        db.reference(f'Employee/{employee_id}').update(updates)
        self.log_access(employee_id, log_status, current_time.strftime('%Y-%m-%d %H:%M:%S'))
        print(f"Check-in completed for employee {employee_id}.")
        return status

    def handle_check_out(self, employee_id, employee_data, current_time):
        """

        """
        updates = {
            "check_out_time": current_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        db.reference(f'Employee/{employee_id}').update(updates)
        self.log_access(employee_id, "Checked Out",  current_time.strftime('%Y-%m-%d %H:%M:%S'))
        print(f"Check-out completed for employee {employee_id}.")
        return "check_out"

    #===========================cloudinary==========================================
    def upload_to_cloudinary(self, image_path, status):
        """
        upload image to Cloudinary.
        :param image_path: path to image upload.
        :param status: unknown or spoof.
        :return: URL of image when upload successful.
        """
        folder = os.path.join(self.cloud_folder, status).replace("\\", "/")
        try:
            response = cloudinary.uploader.upload(
                image_path,
                folder=folder,
                overwrite=True,
                resource_type="image"
            )
            return response['secure_url']
        except Exception as e:
            print(f"Error can't upload image to Cloudinary: {e}")
            return None


