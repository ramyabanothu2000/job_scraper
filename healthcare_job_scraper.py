import pandas as pd
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

# ------------------------------
# CONFIGURATION
# ------------------------------
CSV_FILE = "Healthcare_Data_AI_Jobs_USA.csv"
JOB_SOURCES = [
    "https://www.indeed.com/jobs?q=Data+Engineer+Healthcare&l=",
    "https://builtin.com/jobs/data-analytics/data-engineering/healthtech",
    "https://www.linkedin.com/jobs/search?keywords=Data%20Engineer%20Healthcare",
    "https://www.glassdoor.com/Job/us-healthcare-data-engineer-jobs-SRCH_IL.0,2_IN1_KO3,28.htm"
]

# Email credentials will come from GitHub Secrets
EMAIL_ALERTS = True
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_TO = os.environ.get("EMAIL_TO")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ------------------------------
# HELPER FUNCTIONS
# ------------------------------

def fetch_indeed_jobs():
    jobs = []
    url = JOB_SOURCES[0]
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    for div in soup.find_all("div", class_="job_seen_beacon"):
        title_tag = div.find("h2", class_="jobTitle")
        title = title_tag.text.strip() if title_tag else "N/A"
        link_tag = div.find("a", href=True)
        link = "https://www.indeed.com" + link_tag['href'] if link_tag else ""
        location_tag = div.find("div", class_="companyLocation")
        location = location_tag.text.strip() if location_tag else "N/A"
        date_tag = div.find("span", class_="date")
        date_posted = date_tag.text.strip() if date_tag else "N/A"
        jobs.append({"Company": "Indeed Listing", "Role": title, "Location": location, "Link": link, "Date Posted": date_posted})
    return jobs

def fetch_builtin_jobs():
    jobs = []
    url = JOB_SOURCES[1]
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    for div in soup.find_all("div", class_="job-card"):
        title_tag = div.find("a", class_="job-title")
        title = title_tag.text.strip() if title_tag else "N/A"
        link = "https://builtin.com" + title_tag['href'] if title_tag else ""
        company_tag = div.find("div", class_="company")
        company = company_tag.text.strip() if company_tag else "BuiltIn"
        location_tag = div.find("div", class_="location")
        location = location_tag.text.strip() if location_tag else "Remote"
        jobs.append({"Company": company, "Role": title, "Location": location, "Link": link, "Date Posted": datetime.today().strftime("%Y-%m-%d")})
    return jobs

def fetch_linkedin_jobs():
    jobs = []
    url = JOB_SOURCES[2]
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    for li in soup.find_all("li", class_="result-card"):
        title_tag = li.find("h3", class_="result-card__title")
        title = title_tag.text.strip() if title_tag else "N/A"
        link_tag = li.find("a", class_="result-card__full-card-link")
        link = link_tag['href'] if link_tag else ""
        company_tag = li.find("h4", class_="result-card__subtitle")
        company = company_tag.text.strip() if company_tag else "LinkedIn"
        location_tag = li.find("span", class_="job-result-card__location")
        location = location_tag.text.strip() if location_tag else "Remote"
        jobs.append({"Company": company, "Role": title, "Location": location, "Link": link, "Date Posted": datetime.today().strftime("%Y-%m-%d")})
    return jobs

def fetch_glassdoor_jobs():
    jobs = []
    url = JOB_SOURCES[3]
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    for div in soup.find_all("div", class_="react-job-listing"):
        title_tag = div.find("a", class_="jobLink")
        title = title_tag.text.strip() if title_tag else "N/A"
        link = "https://www.glassdoor.com" + title_tag['href'] if title_tag else ""
        company_tag = div.find("div", class_="jobHeader")
        company = company_tag.text.strip() if company_tag else "Glassdoor"
        location_tag = div.find("span", class_="subtle loc")
        location = location_tag.text.strip() if location_tag else "Remote"
        jobs.append({"Company": company, "Role": title, "Location": location, "Link": link, "Date Posted": datetime.today().strftime("%Y-%m-%d")})
    return jobs

def send_email(new_jobs):
    if not new_jobs or not EMAIL_ALERTS:
        return
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = f"{len(new_jobs)} New Healthcare Data Jobs Added"
    body = "New job postings:\n\n"
    for job in new_jobs:
        body += f"{job['Role']} at {job['Company']} ({job['Location']})\nLink: {job['Link']}\n\n"
    msg.attach(MIMEText(body, 'plain'))
    
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(EMAIL_FROM, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()
    print(f"Email sent with {len(new_jobs)} new jobs.")

# ------------------------------
# MAIN SCRIPT
# ------------------------------

def main():
    jobs_indeed = fetch_indeed_jobs()
    jobs_builtin = fetch_builtin_jobs()
    jobs_linkedin = fetch_linkedin_jobs()
    jobs_glassdoor = fetch_glassdoor_jobs()
    
    all_jobs = jobs_indeed + jobs_builtin + jobs_linkedin + jobs_glassdoor
    
    if os.path.exists(CSV_FILE):
        df_existing = pd.read_csv(CSV_FILE)
        df_existing.drop_duplicates(subset=["Link"], inplace=True)
    else:
        df_existing = pd.DataFrame(columns=["Company","Role","Location","Link","Date Posted"])
    
    df_new = pd.DataFrame(all_jobs)
    combined = pd.concat([df_existing, df_new], ignore_index=True)
    combined.drop_duplicates(subset=["Link"], inplace=True)
    
    new_jobs = df_new[~df_new["Link"].isin(df_existing["Link"])]
    
    combined.to_csv(CSV_FILE, index=False)
    print(f"CSV updated. Total jobs: {len(combined)}. New jobs: {len(new_jobs)}.")
    
    send_email(new_jobs.to_dict('records'))

if __name__ == "__main__":
    main()
