import os
import sys
import json
import webbrowser
from google import genai
from google.genai import types
from dotenv import load_dotenv

def main():
    print("--- AI-Assisted Resume Portfolio Generator ---")
    
    # [Step 1: Place resume content inside resume.txt] 
    
    # [Step 2: Run the Python program] 
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "put_your_actual_api_key_here":
        print("❌ Error: Missing or invalid GEMINI_API_KEY in .env file.")
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)

    # [Step 3: Validate and clean the resume text]
    if not os.path.exists("resume.txt"):
        print("❌ Error: resume.txt is missing. Please create it and add your resume text.")
        sys.exit(1)
        
    with open("resume.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    cleaned_resume_text = "\n".join(cleaned_lines)
    
    if len(cleaned_resume_text) < 50:
        print("❌ Error: resume.txt is empty or too short. Please provide a complete resume.")
        sys.exit(1)

    # [Step 4: Create a structured prompt]
    prompt = """
    You are an AI assistant that extracts resume data and outputs strictly in JSON format.
    Rules:
    1. Use ONLY the information present in the resume. Do NOT invent skills, experience, projects, achievements, companies, dates, or links.
    2. If information is missing for a section, use an empty string "" or an empty list [].
    3. Keep the professional summary concise and factual.
    4. Return ONLY valid JSON, no extra text or markdown formatting.

    Required JSON Structure:
    {
        "name": "Full name",
        "headline": "Short professional identity (e.g. Software Engineer)",
        "summary": "Concise introduction",
        "skills": ["Skill 1", "Skill 2"],
        "education": [ {"degree": "", "institution": "", "year": ""} ],
        "experience": [ {"role": "", "company": "", "duration": "", "responsibilities": ["", ""]} ],
        "projects": [ {"title": "", "description": "", "technologies": [""]} ],
        "achievements": ["Achievement 1"],
        "contact": {"email": "", "phone": "", "linkedin": "", "github": ""}
    }

    Cleaned Resume Text:
    """
    
    print("⏳ Sending resume to Gemini API (using gemini-3.6-flash)...")
    try:
        # [Step 5: Receive portfolio content in JSON format]
        # UPDATED TO GEMINI 3.6 AS REQUESTED BY GOOGLE
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt + cleaned_resume_text,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        json_output = response.text
    except Exception as e:
        print(f"❌ API Error during generation: {e}")
        sys.exit(1)

    # [Step 6: Convert the JSON response into Python data]
    try:
        data = json.loads(json_output)
    except json.JSONDecodeError:
        print("❌ Error: Received invalid JSON from Gemini API. Safely stopping.")
        sys.exit(1)

    # [Step 7: Insert the data into an HTML template]
    print("📄 Generating HTML portfolio...")
    if not os.path.exists("template.html"):
        print("❌ Error: template.html is missing.")
        sys.exit(1)
        
    with open("template.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Replace variables with Python data
    html = html.replace("{{NAME}}", data.get("name", "Portfolio") or "Portfolio")
    html = html.replace("{{HEADLINE}}", data.get("headline", "") or "")

    contact_html = ""
    contact = data.get("contact", {})
    if contact.get("email"): contact_html += f"<p>Email: <a href='mailto:{contact['email']}'>{contact['email']}</a></p>"
    if contact.get("phone"): contact_html += f"<p>Phone: {contact['phone']}</p>"
    if contact.get("linkedin"): contact_html += f"<p>LinkedIn: <a href='{contact['linkedin']}'>{contact['linkedin']}</a></p>"
    if contact.get("github"): contact_html += f"<p>GitHub: <a href='{contact['github']}'>{contact['github']}</a></p>"
    html = html.replace("{{CONTACT_INFO}}", contact_html)

    if data.get("summary"): html = html.replace("{{SUMMARY_SECTION}}", f"<section><h2>Professional Summary</h2><p>{data['summary']}</p></section>")
    else: html = html.replace("{{SUMMARY_SECTION}}", "")

    if data.get("skills"):
        skills_html = "<section><h2>Skills</h2>"
        for skill in data['skills']: skills_html += f"<span class='badge'>{skill}</span>"
        skills_html += "</section>"
        html = html.replace("{{SKILLS_SECTION}}", skills_html)
    else: html = html.replace("{{SKILLS_SECTION}}", "")

    if data.get("experience"):
        exp_html = "<section><h2>Experience</h2>"
        for exp in data['experience']:
            exp_html += f"<h3>{exp.get('role', '')} at {exp.get('company', '')}</h3><p><em>{exp.get('duration', '')}</em></p><ul>"
            for resp in exp.get('responsibilities', []): exp_html += f"<li>{resp}</li>"
            exp_html += "</ul>"
        exp_html += "</section>"
        html = html.replace("{{EXPERIENCE_SECTION}}", exp_html)
    else: html = html.replace("{{EXPERIENCE_SECTION}}", "")

    if data.get("education"):
        edu_html = "<section><h2>Education</h2><ul>"
        for edu in data['education']: edu_html += f"<li><strong>{edu.get('degree', '')}</strong> - {edu.get('institution', '')} ({edu.get('year', '')})</li>"
        edu_html += "</ul></section>"
        html = html.replace("{{EDUCATION_SECTION}}", edu_html)
    else: html = html.replace("{{EDUCATION_SECTION}}", "")

    if data.get("projects"):
        proj_html = "<section><h2>Projects</h2>"
        for proj in data['projects']:
            proj_html += f"<h3>{proj.get('title', '')}</h3><p>{proj.get('description', '')}</p><p><strong>Tech:</strong> " + ", ".join(proj.get('technologies', [])) + "</p>"
        proj_html += "</section>"
        html = html.replace("{{PROJECTS_SECTION}}", proj_html)
    else: html = html.replace("{{PROJECTS_SECTION}}", "")

    if data.get("achievements"):
        ach_html = "<section><h2>Achievements</h2><ul>"
        for ach in data['achievements']: ach_html += f"<li>{ach}</li>"
        ach_html += "</ul></section>"
        html = html.replace("{{ACHIEVEMENTS_SECTION}}", ach_html)
    else: html = html.replace("{{ACHIEVEMENTS_SECTION}}", "")

    # [Step 8: Save the final output]
    with open("portfolio.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("✅ Success! portfolio.html has been generated.")

    # [Step 9: Open browser automatically]
    portfolio_path = os.path.abspath("portfolio.html")
    print("🌐 Automatically opening portfolio in your web browser...")
    webbrowser.open(f"file://{portfolio_path}")

if __name__ == "__main__":
    main()