# AI CV Reviewer

A professional CV analysis tool built with Streamlit and Google Gemini AI. This application evaluates CVs against job descriptions, providing ATS readiness scores, keyword analysis, and actionable improvement suggestions.

---

## 🎯 Complete Feature List

### Core Features
- ✅ **Dual-Page Workflow**: Separate upload page and results page for better UX
- ✅ **Two Analysis Modes**: General Review and ATS Scan with distinct analysis approaches
- ✅ **Automatic Mode Re-analysis**: Change modes on results page without re-uploading
- ✅ **ATS Readiness Scoring**: Comprehensive scoring (0-100%) across multiple dimensions
- ✅ **Keyword Analysis**: Identifies missing keywords from job descriptions
- ✅ **Subscore Breakdown**: Skills alignment, experience alignment, and ATS readiness
- ✅ **Detailed Suggestions**: Actionable improvement recommendations
- ✅ **Report Downloads**: Export analysis as Markdown or JSON
- ✅ **Debug Mode**: View raw AI responses for troubleshooting
- ✅ **CV Text Preview**: Preview extracted CV text before analysis
- ✅ **Session Storage**: CV data stored in session for mode switching

---

## 📋 Complete Workflow

### **Page 1: Upload Page**

#### Step 1: Configure Settings (Top Bar)
- **Mode Selection**: Choose between:
  - 📝 **General Review**: Holistic evaluation focusing on overall quality and content alignment
  - 🔍 **ATS Scan**: Strict keyword matching, format compliance, optimized for automated screening
- **Debug Mode**: Optional checkbox to enable detailed debugging information

#### Step 2: Input Job Description
- Paste the job description in the text area
- Include role requirements, must-have skills, and seniority expectations
- Maximum length: ~4000 characters (automatically truncated)

#### Step 3: Upload CV
- Click "Upload resume (PDF only)" or drag and drop
- Supported format: PDF only
- Maximum file size: 2MB
- Best results with text-based PDFs (not scanned images)

#### Step 4: Analyze
- Click "Upload & analyze" button
- System automatically:
  1. Validates inputs (file size, format)
  2. Extracts text from PDF
  3. Shows CV text preview (first 500 characters)
  4. Displays parse confidence indicator
  5. Sends data to Gemini AI for analysis
  6. Redirects to results page

### **Page 2: Report Page**

#### Automatic Display
- **Header Section**:
  - Resume filename
  - Overall match score (0-100)
  - Mode used for analysis
  - Mode description

#### Sidebar Panel (Left)
- **Score Card**:
  - Overall score (large display)
  - Total issues count
  
- **Category Breakdown**:
  - **Content**: ATS parse rate, quantifying impact, repetition, spelling & grammar
  - **Sections**: Section completeness and structure
  - **ATS Essentials**: ATS-specific requirements
  - **Tailoring**: Job description alignment
  
- **Download Buttons**:
  - Download Markdown report
  - Download JSON export

#### Main Content Panel (Right)
- **ATS Parse Rate Section**:
  - Visual progress bar showing parse rate percentage
  - Explanation of ATS importance
  
- **Strengths Section**:
  - List of identified strengths
  - Badge showing item count
  
- **Missing Skills Section**:
  - Skills from JD not found in CV
  - Warning badge for attention
  
- **Missing Keywords Section**:
  - ATS-relevant keywords missing from CV
  - Critical for ATS optimization
  
- **Suggestions Section**:
  - Numbered list of actionable recommendations
  - Prioritized improvement tips

#### Mode Switching (Live Re-analysis)
- Change mode dropdown in top bar
- System automatically:
  1. Detects mode change
  2. Shows "Re-analyzing..." spinner
  3. Re-runs analysis with new mode
  4. Updates all results instantly
  5. No need to re-upload CV

#### Navigation
- **"Upload another resume"** button: Returns to upload page
- Clears current analysis and starts fresh

---

## 🔄 Detailed Feature Explanations

### **1. Two Analysis Modes**

#### **General Review Mode**
- **Focus**: Holistic, balanced evaluation
- **Scoring Approach**: Considers overall fit, transferable skills, and potential
- **Analysis Includes**:
  - Overall resume quality and professionalism
  - Content relevance and clarity
  - Work history alignment
  - Transferable skills assessment
  - General improvement suggestions
  
**Best For**: Career coaching, resume quality improvement, general feedback

#### **ATS Scan Mode**
- **Focus**: Strict ATS optimization
- **Scoring Approach**: Strict keyword matching and format compliance
- **Analysis Includes**:
  - Comprehensive keyword extraction from JD
  - Keyword matching verification
  - ATS format compliance (sections, headers, formatting)
  - Missing keywords flagged extensively
  - Keyword density analysis
  - Section completeness check
  
**Best For**: Job applications, ATS optimization, keyword optimization

### **2. Automatic Mode Re-analysis**

**How It Works**:
1. CV text and job description are stored in session when first analyzed
2. On report page, mode change is detected automatically
3. System uses stored data to re-analyze without re-uploading
4. Results update instantly with new mode's criteria

**User Experience**:
- Switch modes anytime from the top bar
- See immediate difference in scores and suggestions
- No need to re-upload or re-enter job description

### **3. Debug Mode**

**When Enabled**:
- Shows expandable "Debug: Raw AI Response" section
- Displays:
  - Model name used (e.g., `models/gemini-1.5-flash-latest`)
  - Complete raw AI response before processing
  - Any markdown or formatting in response
- Enhanced error messages with raw response data

**Use Cases**:
- Troubleshooting analysis failures
- Understanding AI behavior
- Development and testing
- Diagnosing JSON parsing issues

### **4. Scoring System**

**Overall Match Score** (0-100):
- Weighted combination of all subscores
- Color-coded display:
  - 🟢 80-100: Excellent fit
  - 🟡 60-79: Good fit
  - 🔴 0-59: Needs improvement

**Subscores**:
- **Skills Alignment** (0-100): How well CV skills match JD requirements
- **Experience Alignment** (0-100): Relevance of work history to job requirements
- **ATS Readiness** (0-100): Likelihood of passing ATS screening

**Issues Count**:
- Total number of problems identified
- Includes missing keywords, missing skills, and suggestion items

### **5. Report Downloads**

**Markdown Report**:
- Formatted text document
- Includes all scores, strengths, gaps, and suggestions
- Human-readable format
- Suitable for sharing or printing

**JSON Export**:
- Complete analysis data in JSON format
- Includes all structured data
- Suitable for programmatic use
- API integration or further processing

---

## 🏗️ Project Structure

```
cv-review/
├── app.py                 # Main Streamlit application entry point
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .env                  # Your environment variables (not in git)
├── README.md             # This documentation
├── PRD_CV.txt           # Product Requirements Document
├── templates/            # HTML template references
│   ├── resume_checker.html      # Upload page HTML template
│   └── resume_report_page.html  # Report page HTML template
└── src/                  # Source code modules
    ├── __init__.py
    ├── config.py        # Configuration and environment setup
    ├── pdf_utils.py     # PDF text extraction utilities
    ├── gemini_client.py # Gemini AI integration and analysis
    ├── reporting.py     # Markdown report generation
    └── ui_components.py # Streamlit UI components and styling
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation Steps

1. **Clone or download the project**
```bash
cd cv-review
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env and add your API key
GOOGLE_API_KEY=your-api-key-here
GEMINI_MODEL=models/gemini-2.0-flash-exp  # Optional
```

4. **Run the application**
```bash
streamlit run app.py
```

5. **Access the application**
- Open browser to `http://localhost:8501`
- Start analyzing CVs!

### Run automated tests
```bash
py -3 -m unittest discover -s tests -v
```

---

## ⚙️ Configuration

### Environment Variables

**Required**:
- `GOOGLE_API_KEY`: Your Google Gemini API key (required)

**Optional**:
- `GEMINI_MODEL`: Preferred Gemini model name
  - Examples:
    - `models/gemini-2.0-flash-exp` (experimental, latest)
    - `models/gemini-1.5-flash-latest` (stable, recommended)
    - `models/gemini-1.5-pro` (more powerful, slower)
  - If not set, system uses fallback chain

### File Size Limits
- Maximum CV file size: 2MB (matches industry standards for resume checkers)
- CV text truncation: First 6000 characters sent to AI
- Job description truncation: First 4000 characters sent to AI

---

## 📖 Usage Examples

### Example 1: First-Time User
1. Open application
2. Select "General Review" mode
3. Paste job description
4. Upload CV
5. Click "Upload & analyze"
6. Review comprehensive feedback
7. Download report

### Example 2: ATS Optimization
1. Upload CV and JD
2. Run analysis in "General Review" mode
3. Switch to "ATS Scan" mode (automatic re-analysis)
4. Compare scores - ATS Scan typically shows lower scores
5. Focus on missing keywords section
6. Update CV with missing keywords
7. Re-analyze to verify improvement

### Example 3: Mode Comparison
1. Analyze CV in "General Review" mode
2. Note the score and suggestions
3. Switch to "ATS Scan" mode
4. Compare:
   - Score difference
   - Missing keywords (more extensive in ATS mode)
   - Suggestion focus (ATS vs general)

---

## 🐛 Troubleshooting

### Common Issues

**"AI response was not in expected JSON format"**
- Enable Debug Mode to see raw response
- Check if API key is valid
- Try a different model in `.env`

**PDF extraction fails**
- Ensure PDF is text-based (not scanned image)
- Check file isn't corrupted
- Try converting PDF to text-based format

**Analysis takes too long**
- Check internet connection
- API rate limits may apply
- Try a faster model (flash instead of pro)

**Mode switching doesn't work**
- Ensure you're on the report page
- Check that initial analysis completed successfully
- Refresh page and re-upload if needed

---

## 🔧 Technical Details

### Technology Stack
- **Frontend**: Streamlit
- **AI Model**: Google Gemini (via `google-generativeai`)
- **PDF Processing**: PyPDF2
- **Configuration**: python-dotenv

### Key Components

**app.py**:
- Main application logic
- Two-page workflow management
- Session state management
- Mode switching logic

**src/gemini_client.py**:
- AI integration
- Prompt engineering for both modes
- JSON parsing and extraction
- Error handling

**src/ui_components.py**:
- Modern dark-themed UI
- Report page layout
- Upload page preview
- Download button implementation

**src/pdf_utils.py**:
- PDF text extraction
- Parse confidence detection
- File validation

**src/config.py**:
- Environment variable handling
- Model selection logic
- Configuration constants

---

## 📝 Development Notes

### Session State Variables
- `page`: Current page ("upload" or "report")
- `analysis`: Analysis results dictionary
- `cv_name`: Uploaded CV filename
- `cv_text`: Extracted CV text (for re-analysis)
- `job_description`: Job description text (for re-analysis)
- `analysis_mode`: Mode used for current analysis
- `mode`: Currently selected mode
- `debug`: Debug mode enabled/disabled
- `issues`: Total issue count

### Analysis Data Structure
```json
{
  "match_score": 85,
  "strengths": ["string1", "string2"],
  "missing_skills": ["skill1", "skill2"],
  "suggestions": ["suggestion1", "suggestion2"],
  "subscores": {
    "skills_alignment": 80,
    "experience_alignment": 75,
    "ats_readiness": 90
  },
  "missing_keywords": ["keyword1", "keyword2"]
}
```

---

## 📄 License

This project is for educational purposes (college project submission).

---

## 👤 Author

Built as a college project submission.

---

## 🎓 Features Summary Table

| Feature | Description | Status |
|---------|-------------|--------|
| Dual-page workflow | Separate upload and results pages | ✅ |
| Two analysis modes | General Review & ATS Scan | ✅ |
| Live mode switching | Re-analyze without re-uploading | ✅ |
| ATS scoring | Comprehensive 0-100 scoring | ✅ |
| Keyword analysis | Missing keywords detection | ✅ |
| Subscore breakdown | Skills, experience, ATS readiness | ✅ |
| Report downloads | Markdown & JSON export | ✅ |
| Debug mode | Raw AI response viewing | ✅ |
| CV preview | Text extraction preview | ✅ |
| Session storage | Data persistence for re-analysis | ✅ |
| Error handling | Comprehensive error messages | ✅ |
| Modern UI | Dark-themed, professional design | ✅ |

---

**Last Updated**: Current version with all features implemented

