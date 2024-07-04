# Copyright (c) 2024, Aerele and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from bs4 import BeautifulSoup

import pandas as pd
import chardet

from frappe.utils import cstr

class JVImport(Document):
	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		attach_file: DF.Attach | None
		company: DF.Link | None
		import_file_type: DF.Literal["HTML", "TEXT"]
		journal_type: DF.Literal["Journal Entry", "Inter Company Journal Entry", "Bank Entry", "Cash Entry", "Credit Card Entry", "Debit Note", "Credit Note", "Contra Entry", "Excise Entry", "Write Off Entry", "Opening Entry", "Depreciation Entry", "Exchange Rate Revaluation", "Exchange Gain Or Loss", "Deferred Revenue", "Deferred Expense"]
		posting_date: DF.Date | None
		skip_total: DF.Int
		status: DF.Literal["Pending", "Failed", "Partially Imported", "Imported"]

	@frappe.whitelist()
	def import_data(self):
		if not self.attach_file: return

		import_count = 0
		bulk_data = []
		try:
			if self.import_file_type == "HTML" and self.attach_file.split('.')[-1].lower() in ['xls', 'xlsx', 'csv']:
				bulk_data = self.get_bulk_html_to_dict_list()
			elif self.import_file_type == "HTML" and self.attach_file.split('.')[-1].lower() not in ['xls', 'xlsx', 'csv']:
				frappe.throw(title= "Invalid File Type", msg="Please select a ['xls', 'xlsx', 'csv', 'html'] file to import")

			if self.import_file_type == "HTML" and self.attach_file.split('.')[-1].lower() == 'html':
				bulk_data =  [self.get_html_to_dict()]
			elif self.import_file_type == "HTML" and self.attach_file.split('.')[-1].lower() not in ['html','xls', 'xlsx', 'csv']:
				frappe.throw(title= "Invalid File Type", msg="Please select a HTML file to import")

			if self.import_file_type == "TEXT" and self.attach_file.split('.')[-1].lower()  == "txt":
				bulk_data =  [self.get_text_to_dict()]
			elif self.import_file_type == "TEXT" and self.attach_file.split('.')[-1].lower() not in ['txt']:
				frappe.throw(title="Invalid File Type", msg="Please select a TEXT file to import")

			if not bulk_data: return


			for data in bulk_data:
				if not data: continue
				try:
					jv = frappe.new_doc("Journal Entry")
					jv.voucher_type = self.journal_type
					jv.company = self.company
					jv.posting_date = self.posting_date

					for d in data:
						acc_data = list(d.values())
						if self.import_file_type == "HTML":
							account = ''
							if acc_data[1]:
								account = frappe.db.get_value("Account", {"account_number": acc_data[1]}, "name")
								if not account:
									raise frappe.exceptions.DoesNotExistError(f"Account <b>{acc_data[1]}</b> not found in the system. Please create the account first.")
							else:
								frappe.log_error(reference_doctype="JV Import", reference_name=self.name, message=cstr(acc_data), title="JV Import Error")
								raise frappe.exceptions.DoesNotExistError("Please provide a valid account for the transaction.")

							jv.append("accounts",
							{
								"user_remark": acc_data[0],
								"account": account,
								"debit": acc_data[2],
								"debit_in_account_currency": acc_data[2],
								"credit": acc_data[3],
								"credit_in_account_currency": acc_data[3]
							})
						elif self.import_file_type == "TEXT":
							account = ''
							if acc_data[1]:
								account = frappe.db.get_value("Account", {"account_number": acc_data[1]}, "name")
								if not account:
									raise frappe.exceptions.DoesNotExistError(f"Account <b>{acc_data[1]}</b> not found in the system. Please create the account first.")

							elif acc_data[2]:
								account = frappe.db.get_value("Account", {"account_number": acc_data[2]}, "name")
								if not account:
									raise frappe.exceptions.DoesNotExistError(f"Account <b>{acc_data[2]}</b> not found in the system. Please create the account first.")
							else:
								frappe.log_error(reference_doctype="JV Import", reference_name=self.name, message=cstr(acc_data), title="JV Import Error")
								raise frappe.exceptions.DoesNotExistError("Please provide a valid account for the transaction.")

							jv.append("accounts",
							{
								"user_remark": acc_data[3] + " " + acc_data[4],
								"account": account,
								"debit": acc_data[5] if acc_data[1] else 0,
								"debit_in_account_currency": acc_data[5] if acc_data[1] else 0,
								"credit": acc_data[5] if not acc_data[1] else 0,
								"credit_in_account_currency": acc_data[5] if not acc_data[1] else 0
							})
					jv.insert(ignore_mandatory=True, ignore_permissions=True, ignore_links=True)
				except:
					frappe.log_error(reference_doctype="JV Import", reference_name=self.name, message=frappe.get_traceback(), title="JV Import Error")
					self.db_set("status", "Partially Imported")
				else:
					import_count += 1
					self.db_set("status", "Imported")
					
		except Exception as e:
			frappe.log_error(reference_doctype="JV Import", reference_name=self.name, message=frappe.get_traceback(), title="JV Import Fail")
			self.db_set("status", "Failed")

	@frappe.whitelist()
	def preview_data(self):
		if not self.attach_file: return
		bulk_data = []
		if self.import_file_type == "HTML" and self.attach_file.split('.')[-1].lower() in ['xls', 'xlsx', 'csv']:
			bulk_data = self.get_bulk_html_to_dict_list()
		elif self.import_file_type == "HTML" and self.attach_file.split('.')[-1].lower() not in ['xls', 'xlsx', 'csv']:
			frappe.throw(title= "Invalid File Type", msg="Please select a ['xls', 'xlsx', 'csv', 'html'] file to import")

		if self.import_file_type == "HTML" and self.attach_file.split('.')[-1].lower() == 'html':
			bulk_data =  [self.get_html_to_dict()]
		elif self.import_file_type == "HTML" and self.attach_file.split('.')[-1].lower() not in ['html', 'xls', 'xlsx', 'csv']:
			frappe.throw(title= "Invalid File Type", msg="Please select a HTML file to import")

		if self.import_file_type == "TEXT" and self.attach_file.split('.')[-1].lower()  == "txt":
			bulk_data =  [self.get_text_to_dict()]
		elif self.import_file_type == "TEXT" and self.attach_file.split('.')[-1].lower() not in ['txt']:
			frappe.throw(title="Invalid File Type", msg="Please select a TEXT file to import")

		if not bulk_data: return

		html = ''
		for data in bulk_data:
			# Create HTML table headers
			headers = data[0].keys()

			# Start HTML string
			html = '''
			<style>
				table {
					border-collapse: collapse;
					width: 100%;
					text-align: left;
				}

				th, td {
					padding: 8px;
					border: 1px solid #ddd;
				}

				tr:nth-child(even) {
					background-color: #f2f2f2;
				}

				th {
					background-color: #282828;
					color: white;
			</style>
			<table>\n'''

			# Create the header row
			html += '  <tr>\n'
			for header in headers:
				html += f'    <th>{header}</th>\n'
			html += '  </tr>\n'

			# Create the data rows
			for row in data:
				html += '  <tr>\n'
				for header in headers:
					html += f'    <td>{row[header]}</td>\n'
				html += '  </tr>\n'

			# End HTML string
			html += '</table><br><br>'

		return html

	
	def get_html_to_dict(self, file_content=None):
		if not self.attach_file or file_content: return
		file_doc = frappe.get_doc("File", {"file_url": self.attach_file})
		file_path = file_doc.get_full_path()
		html = ''
		if file_doc.file_type == "HTML":
			file = open(file_path, 'r', encoding='ISO-8859-1')
			html = file.read()
		elif file_content:
			html = file_content
		else:
			frappe.throw({"title": "Invalid File Type", "message": f"Please select an HTML file to import."})


		soup = BeautifulSoup(html, 'html.parser')

		# Extract headers from the first two rows and concatenate their values
		skip_header = self.no_of_rows if self.exclude_header and self.no_of_rows else 0
		header_rows = soup.find_all('tr')[:skip_header]
		self.headers = []
		if skip_header:
			for col1, col2 in zip(header_rows[0].find_all('td'), header_rows[1].find_all('td')):
				header = col1.get_text(strip=True).replace(':', '') + ' ' + col2.get_text(strip=True)
				self.headers.append(header.strip())
		else:
			self.headers = ['Description', 'Account', 'Debit', 'Credit']

		# Extract rows
		rows = soup.find_all('tr')[self.skip_header or 2:]

		data = []
		for row in rows:
			cols = row.find_all('td')
			row_data = [col.get_text(strip=True) for col in cols]
			data.append(row_data)

		# Convert to dictionary format
		dict_data = []
		for row in data[:(-self.skip_total) or len(data)]:
			entry = {}
			for i in range(len(self.headers)):
				if i < len(row):
					entry[self.headers[i]] = row[i]
				else:
					entry[self.headers[i]] = ''
			dict_data.append(entry)

		if not dict_data:
			frappe.throw({"title": "No Data Found", "message": f"No data found in the file. Please check the file format and try again."})

		return dict_data
	
	def get_text_to_dict(self):
		if not self.attach_file: return
		# Read the text content
		file_path = frappe.get_doc("File", {"file_url": self.attach_file}).get_full_path()
		file = open(file_path, 'r', encoding="ISO-8859-1")
		text = file.read()

		# Split the text into rows
		rows = text.split('\n')

		skip_header = 0
		# Extract headers from the first row
		if self.exclude_header and self.no_of_rows:
			skip_header = self.no_of_rows
			if len(rows) <= self.no_of_rows:
				frappe.throw(title ="No Data Found",msg="No data found in the file. Please check the file format and try again.")
			columns_count = len(rows[0].split('\t'))
			header_columns = [[row for row in rows[0].split('\t') if row.strip()]]
			for header in rows[1:self.no_of_rows]:
				if len(header.split('\t')) <= columns_count:
					try:
						header_columns.append([str(head1) + " " +str(head2) for head1, head2 in zip(header_columns[-1], header.split('\t'))])
					except:
						c = len(header.split('\t'))
						inv_head = [str(head1) + " " +str(head2) for head1, head2 in zip(header_columns[-1][:c], header.split('\t'))]
						header_columns[-1][:len(inv_head)] = inv_head
				else:
					header_columns.append([str(head1) + " " +str(head2) for head1, head2 in zip(header_columns[-1], header.split('\t'))])

			headers = header_columns[-1]
		else:
			headers = ['Date', 'Account(Dr)', 'Account(Cr)', 'Description1', 'Description2', 'Amount']

		# Extract data rows
		data = []
		for row in rows[skip_header:]:
			cols = row.split('\t')
			if len(cols) == len(headers):
				row_data = [col.strip() for col in cols]
			elif len(cols) < len(headers):
				empty_cols = [' ' for c in range(len(headers) - len(cols))]
				row_data = [col.strip() for col in cols] + empty_cols
			else:
				len_head = len(headers)
				row_data = [col.strip() for col in cols[:len_head]]

			if row_data and not row_data[0]:
				continue
			data.append(row_data)

		# Convert to dictionary format
		dict_data = []
		for row in data:

			entry = {}
			for i in range(len(headers)):
				if i < len(row):
					entry[headers[i]] = row[i]
				else:
					entry[headers[i]] = ''
			dict_data.append(entry)

		return dict_data

	def get_bulk_html_to_dict_list(self):
		if not self.attach_file: return
		# Read the text content
		file_path = frappe.get_doc("File", {"file_url": self.attach_file}).get_full_path()
		encoding = ''
		with open(file_path, 'rb') as file:
			result = chardet.detect(file.read())
    
		encoding = result['encoding']

		data = []

		def _get_tables_data(tables):
			for table in tables:
				df = table

				# Drop completely empty columns
				df.dropna(axis=1, how='all', inplace=True)

				# Rename the columns based on the second row (index 1)
				df.columns = df.iloc[1]

				# Drop the first two rows since they are headers and empty rows
				header_rows = list(range(self.no_of_rows)) if self.exclude_header and self.no_of_rows else [0, 1]
				df = df.drop(header_rows)

				# Reset the index
				df.reset_index(drop=True, inplace=True)

				# Convert the dataframe to a list of dictionaries
				data_list = df.to_dict(orient='records')

				for row in data_list:
					for key, value in row.items():
						if pd.isna(value):
							row[key] = 0

				if data_list:
					data.append(data_list[:(-1) or len(data_list)])

		if self.import_file_type == "HTML" and self.attach_file.split('.')[-1].lower() == 'csv':
			tables =  pd.read_html(file_path, encoding=encoding)
			_get_tables_data(tables)

		elif self.import_file_type == "HTML" and self.attach_file.split('.')[-1].lower() == 'xlsx':
			tables =  pd.read_html(file_path, encoding=encoding)
			_get_tables_data(tables)

		elif self.import_file_type == "HTML" and self.attach_file.split('.')[-1].lower() == 'xls':
			#reading xls file using openpyxl engine
			tables =  pd.read_html(file_path, encoding=encoding)


			# Extract data from the list of tables
			_get_tables_data(tables)

		return data
	
	@frappe.whitelist()
	def preview_error_log(self):
		html = ""
		for data in frappe.db.get_all('Error Log', filters={'reference_doctype': 'JV Import', 'reference_name': self.name}, fields=['error']):
			html +=  get_preview_from_template(data)
		return html
			

def get_preview_from_template(data):
	template = """
		<style>
			.collapsible_c {
				background-color: #e0382c;
				color: white;
				cursor: pointer;
				padding: 5px 5px;
				border: none;
				text-align: left;
				outline: none;
				font-size: 12px;
				border-radius: 5px;
				margin: 5px 0;
			}

			.active_c, .collapsible_c:hover {
				background-color: #1f1f1f;
			}

			.content_c {
				padding: 15px;
				display: none;
				overflow: hidden;
				background-color: white;
				border: 1px solid #ddd;
				border-radius: 5px;
				box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
			}
		</style>
		<button class="collapsible_c">Show error</button>
		<div class="content_c">
		<p style= "border: 1px solid #ddd; padding: 10px; background-color: #f2f2f2; border-radius: 5px; margin-bottom: 10px;">
		"""
	template+= data.error
	template +="</p></div>"
	return r""+template+""
