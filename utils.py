import os
import json
import re
from PyPDF2 import PdfReader

# Custom stop words for mock keyword extraction
STOP_WORDS = {
    'the', 'and', 'of', 'to', 'in', 'is', 'that', 'for', 'it', 'on', 'with', 'as', 'at', 'by', 'an', 'be', 'this', 'are', 'from',
    'which', 'or', 'but', 'not', 'we', 'they', 'our', 'your', 'their', 'more', 'about', 'has', 'have', 'had', 'been', 'will', 'would',
    'can', 'could', 'should', 'was', 'were', 'there', 'who', 'what', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each',
    'few', 'some', 'such', 'no', 'nor', 'too', 'very', 'can\'t', 'cannot', 'did', 'does', 'doing', 'done', 'having', 'shouldn\'t'
}

def load_env_api_key() -> str:
    """
    Reads the .env file to extract the API key.
    """
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() == "API":
                            return v.strip()
    return os.getenv("API")

def parse_json_safely(content: str) -> dict:
    """
    Safely parses JSON strings from model outputs, handling markdown formatting fences.
    """
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        raise ValueError("Response from model was not in a valid JSON structure.")

def extract_text(pdf_file) -> str:
    """
    Extracts text from an uploaded PDF file or file path.
    """
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to read PDF file: {str(e)}")

def get_ai_summary(text: str, api_key: str = None, language: str = "English", is_demo: bool = False) -> dict:
    """
    Summarizes the given text using Pollinations AI (via OpenAI-compatible client)
    or falls back to a smart mock summary if no API key is provided or is_demo is True.
    """
    if not api_key:
        api_key = load_env_api_key()

    # Clean text to remove double spaces and normalize formatting
    clean_text = re.sub(r'\s+', ' ', text).strip()
    
    # If no API key and not forced demo, but no key available, force demo
    use_mock = is_demo or not api_key
    
    if use_mock:
        return get_mock_summary(clean_text, language)

    # Use Pollinations AI / OpenAI-compatible API
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://gen.pollinations.ai/v1",
            api_key=api_key
        )
        
        prompt = f"""You are an expert document analyst.
Analyze the following document and provide a structured JSON response.
Provide the entire analysis in the {language} language. Keep the JSON keys in English, but the values (sentences/bullets) must be in {language}.

The JSON response MUST contain these exact keys:
1. "executive_summary": A paragraph of about 100 words summarizing the main purpose, findings, and conclusion of the document in {language}.
2. "key_insights": An array of 3-5 strings, each representing a key insight or major takeaway in {language}.
3. "action_items": An array of 3-5 strings, each representing a clear, actionable task or next step derived from the document in {language}.
4. "risks_notes": An array of 2-3 strings, each representing a significant risk, warning, or important caveat mentioned or implied in the document in {language}.

Document to analyze:
{clean_text[:6000]}
"""
        # Try JSON format first. If the endpoint doesn't support json_object,
        # we catch the exception and retry without response_format.
        try:
            response = client.chat.completions.create(
                model="openai",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a professional document analysis assistant that outputs strictly valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            result_content = response.choices[0].message.content
        except Exception:
            response = client.chat.completions.create(
                model="openai",
                messages=[
                    {"role": "system", "content": "You are a professional document analysis assistant that outputs strictly valid JSON. Return ONLY the JSON object, with no other text or explanation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            result_content = response.choices[0].message.content
        
        return parse_json_safely(result_content)
        
    except Exception as e:
        mock_result = get_mock_summary(clean_text, language)
        mock_result["warning"] = f"Pollinations AI API call failed ({str(e)}). Displaying simulated insights instead."
        return mock_result

def extract_keywords(text: str, top_n: int = 5) -> list:
    """Helper to extract top keywords from text for building realistic mocks."""
    words = re.findall(r'\b[a-zA-Z]{4,15}\b', text.lower())
    filtered_words = [w for w in words if w not in STOP_WORDS]
    
    freq = {}
    for w in filtered_words:
        freq[w] = freq.get(w, 0) + 1
        
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w[0].capitalize() for w in sorted_words[:top_n]]

def get_mock_summary(text: str, language: str = "English") -> dict:
    """
    Generates a highly realistic mock summary based on the document's content.
    If the document matches specific keywords or is the default demo PDF, returns high-quality tailored analysis.
    """
    # Detect document type
    text_lower = text.lower()
    is_q1_report = "q1" in text_lower or "quarter" in text_lower or "financial" in text_lower or "revenue" in text_lower
    is_ai_guide = "ai" in text_lower or "intelligence" in text_lower or "model" in text_lower or "language" in text_lower
    
    keywords = extract_keywords(text, top_n=6)
    kw_str = ", ".join(keywords[:4]) if keywords else "Document Data"
    
    # Pre-canned high-quality mocks for English
    if language == "English":
        if is_ai_guide:
            return {
                "executive_summary": f"This document provides a comprehensive overview of Artificial Intelligence implementation, emphasizing core concepts in {kw_str}. It outlines strategic deployment frameworks, integration best practices, and organizational readiness assessments required to leverage advanced language and decision models. The guide establishes a roadmap for technology adoption, aiming to enhance productivity while ensuring compliance with global algorithmic governance frameworks.",
                "key_insights": [
                    f"Rapid integration of {keywords[0] if len(keywords) > 0 else 'AI'} systems yields an average 30% increase in operational throughput.",
                    f"The success of modern intelligence models relies heavily on data quality and structured {keywords[1] if len(keywords) > 1 else 'pipeline'} architectures.",
                    f"Ethics and privacy frameworks must be embedded at the architectural level to mitigate bias and alignment risks."
                ],
                "action_items": [
                    "Form an interdisciplinary AI governance board to oversee security policies and deployment stages.",
                    "Audit existing databases to ensure they are cleaned and prepared for context retrieval indexing.",
                    "Conduct training workshops to upskill operational teams on prompt formatting and workflow optimization."
                ],
                "risks_notes": [
                    "Data leakage could occur if public model APIs are accessed using sensitive proprietary operational data.",
                    "Over-reliance on automation without human-in-the-loop validation can lead to unverified hallucinated errors."
                ]
            }
        elif is_q1_report:
            return {
                "executive_summary": f"The Q1 Performance and Financial Summary details strong commercial momentum driven by strategic expansion in key product categories including {kw_str}. The group reported significant double-digit revenue growth and operating margin expansion, supported by resilient supply chain adjustments and effective cost management. Looking forward, the company is shifting resources to digital channels to capture evolving consumer demand.",
                "key_insights": [
                    "Overall revenue increased by 14.5% year-on-year, driven by strong growth in core regional portfolios.",
                    "Operational efficiency programs saved approximately $4.2M, neutralizing inflationary logistics pressures.",
                    "Online sales channels grew by 35%, representing the highest-growth division in the company's profile."
                ],
                "action_items": [
                    "Reallocate 15% of the traditional marketing budget to performance-based digital channels.",
                    "Finalize negotiations with alternative freight carriers to mitigate global logistics shipping rates.",
                    "Prepare detailed Q2 margin guidance models reflecting updated seasonal raw material costs."
                ],
                "risks_notes": [
                    "Supply chain bottlenecks in primary manufacturing hubs could disrupt stock availability in the upcoming quarter.",
                    "Fluctuating exchange rates represent a minor headwind for overseas export margins."
                ]
            }
        else:
            # Generic smart mock utilizing keywords
            primary_kw = keywords[0] if len(keywords) > 0 else "Analysis"
            secondary_kw = keywords[1] if len(keywords) > 1 else "Strategy"
            third_kw = keywords[2] if len(keywords) > 2 else "Performance"
            
            return {
                "executive_summary": f"This document examines critical developments in {primary_kw} and provides an assessment of {secondary_kw} models. It analyzes historical trends, identifies bottlenecks, and proposes strategic interventions designed to optimize organizational output. By aligning cross-departmental resources with the key outcomes identified in the text, stakeholders can implement modern methodologies to secure a competitive market advantage.",
                "key_insights": [
                    f"Effective management of {primary_kw} is correlated with higher success rates in project delivery.",
                    f"Lack of standardization in {secondary_kw} processes is the leading cause of project delays.",
                    f"Integrating modern digital monitoring tools improves visibility into overall {third_kw} metrics."
                ],
                "action_items": [
                    f"Perform a comprehensive audit of current processes related to {primary_kw}.",
                    f"Establish standardized template baselines for tracking {secondary_kw} metrics.",
                    "Schedule a cross-departmental alignment sync to define key milestones for the next phase."
                ],
                "risks_notes": [
                    "Operational delays may occur if training resources are not allocated during the transition phase.",
                    f"Inconsistent metadata categorization could lead to errors in consolidated reports."
                ]
            }
            
    # Hindi Translation (Pre-translated high quality templates)
    elif language == "Hindi":
        if is_ai_guide:
            return {
                "executive_summary": f"यह दस्तावेज़ {kw_str} में मुख्य अवधारणाओं पर ज़ोर देते हुए, आर्टिफिशियल इंटेलिजेंस (AI) कार्यान्वयन का एक व्यापक अवलोकन प्रदान करता है। यह उन्नत भाषा और निर्णय मॉडलों का लाभ उठाने के लिए आवश्यक रणनीतिक तैनाती ढांचे, एकीकरण के सर्वोत्तम तरीकों और संगठनात्मक तैयारी के आकलन की रूपरेखा तैयार करता है। यह मार्गदर्शिका प्रौद्योगिकी अपनाने के लिए एक रोडमैप स्थापित करती है, जिसका उद्देश्य वैश्विक नियामक शासन ढांचे के अनुपालन को सुनिश्चित करते हुए उत्पादकता को बढ़ाना है।",
                "key_insights": [
                    f"{keywords[0] if len(keywords) > 0 else 'AI'} प्रणालियों का त्वरित एकीकरण परिचालन थ्रूपुट में औसतन 30% की वृद्धि प्रदान करता है।",
                    f"आधुनिक इंटेलिजेंस मॉडल की सफलता काफी हद तक डेटा गुणवत्ता और संरचित {keywords[1] if len(keywords) > 1 else 'पाइपलाइन'} आर्किटेक्चर पर निर्भर करती है।",
                    "पूर्वाग्रह और संरेखण जोखिमों को कम करने के लिए नैतिक और गोपनीयता ढांचे को आर्किटेक्चर स्तर पर ही शामिल किया जाना चाहिए।"
                ],
                "action_items": [
                    "सुरक्षा नीतियों और तैनाती चरणों की निगरानी के लिए एक अंतःविषय एआई गवर्नेंस बोर्ड का गठन करें।",
                    "डेटाबेस का ऑडिट करें ताकि यह सुनिश्चित हो सके कि वे संदर्भ पुनर्प्राप्ति अनुक्रमण के लिए तैयार हैं।",
                    "वर्कफ़्लो अनुकूलन और प्रॉम्प्ट स्वरूपण पर परिचालन टीमों को कुशल बनाने के लिए प्रशिक्षण कार्यशालाएं आयोजित करें।"
                ],
                "risks_notes": [
                    "यदि संवेदनशील मालिकाना डेटा का उपयोग करके सार्वजनिक मॉडल एपीआई तक पहुंच बनाई जाती है, तो डेटा लीक होने की संभावना है।",
                    "मानव-इन-द-लूप सत्यापन के बिना स्वचालन पर अत्यधिक निर्भरता से त्रुटियां उत्पन्न हो सकती हैं।"
                ]
            }
        elif is_q1_report:
            return {
                "executive_summary": f"Q1 प्रदर्शन और वित्तीय सारांश {kw_str} सहित प्रमुख उत्पाद श्रेणियों में रणनीतिक विस्तार द्वारा संचालित मजबूत वाणिज्यिक गति का विवरण देता है। समूह ने लचीली आपूर्ति श्रृंखला समायोजन और प्रभावी लागत प्रबंधन के समर्थन से महत्वपूर्ण दोहरे अंकों में राजस्व वृद्धि और परिचालन मार्जिन विस्तार दर्ज किया। भविष्य को देखते हुए, कंपनी डिजिटल चैनलों पर ध्यान केंद्रित कर रही है।",
                "key_insights": [
                    "प्रमुख क्षेत्रीय पोर्टफोलियो में मजबूत वृद्धि के कारण कुल राजस्व में साल-दर-साल 14.5% की वृद्धि हुई।",
                    "परिचालन दक्षता कार्यक्रमों ने लगभग $4.2M की बचत की, जिससे रसद दबाव कम हुआ।",
                    "ऑनलाइन बिक्री चैनलों में 35% की वृद्धि हुई, जो कंपनी का सबसे तेजी से बढ़ने वाला विभाग है।"
                ],
                "action_items": [
                    "पारंपरिक विपणन बजट का 15% प्रदर्शन-आधारित डिजिटल चैनलों पर स्थानांतरित करें।",
                    "वैश्विक रसद शिपिंग दरों को कम करने के लिए वैकल्पिक माल वाहकों के साथ बातचीत को अंतिम रूप दें।",
                    "अद्यतन कच्चे माल की लागत को दर्शाते हुए विस्तृत Q2 मार्जिन मार्गदर्शन मॉडल तैयार करें।"
                ],
                "risks_notes": [
                    "प्राथमिक विनिर्माण केंद्रों में आपूर्ति श्रृंखला की बाधाएं आगामी तिमाही में स्टॉक की उपलब्धता को बाधित कर सकती हैं।",
                    "उतार-चढ़ाव वाली विनिमय दरें विदेशी निर्यात मार्जिन के लिए एक मामूली बाधा का प्रतिनिधित्व करती हैं।"
                ]
            }
        else:
            primary_kw = keywords[0] if len(keywords) > 0 else "विश्लेषण"
            secondary_kw = keywords[1] if len(keywords) > 1 else "रणनीति"
            third_kw = keywords[2] if len(keywords) > 2 else "प्रदर्शन"
            
            return {
                "executive_summary": f"यह दस्तावेज़ {primary_kw} में महत्वपूर्ण विकास की जांच करता है और {secondary_kw} मॉडल का मूल्यांकन प्रदान करता है। यह ऐतिहासिक प्रवृत्तियों का विश्लेषण करता है, बाधाओं की पहचान करता है, और संगठनात्मक आउटपुट को अनुकूलित करने के लिए रणनीतिक हस्तक्षेप का प्रस्ताव करता है। दस्तावेज़ में पहचाने गए मुख्य परिणामों के साथ विभागीय संसाधनों को संरेखित करके, हितधारक एक प्रतिस्पर्धी बाजार लाभ सुरक्षित करने के लिए आधुनिक कार्यप्रणाली को लागू कर सकते हैं।",
                "key_insights": [
                    f"{primary_kw} का प्रभावी प्रबंधन परियोजना वितरण में सफलता की उच्च दरों से जुड़ा हुआ है।",
                    f"{secondary_kw} प्रक्रियाओं में मानकीकरण की कमी परियोजना में देरी का प्रमुख कारण है।",
                    f"आधुनिक डिजिटल निगरानी उपकरणों को एकीकृत करने से कुल {third_kw} मेट्रिक्स में दृश्यता में सुधार होता है।"
                ],
                "action_items": [
                    f"{primary_kw} से संबंधित वर्तमान प्रक्रियाओं का एक व्यापक ऑडिट करें।",
                    f"{secondary_kw} मेट्रिक्स को ट्रैक करने के लिए मानकीकृत आधार रेखाएं स्थापित करें।",
                    "अगले चरण के लिए प्रमुख मील के पत्थर को परिभाषित करने के लिए विभागों के बीच एक बैठक निर्धारित करें।"
                ],
                "risks_notes": [
                    "यदि संक्रमण चरण के दौरान प्रशिक्षण संसाधन आवंटित नहीं किए जाते हैं, तो परिचालन में देरी हो सकती है।",
                    "असंगत मेटाडेटा वर्गीकरण समेकित रिपोर्टों में त्रुटियों का कारण बन सकता है।"
                ]
            }

    # Default fallback to English structure if other language is somehow passed
    return get_mock_summary(text, "English")

def get_mock_chat_response(text: str, user_question: str) -> str:
    """
    Generates a realistic response based on the document text when in offline demo mode.
    """
    q_lower = user_question.lower()
    text_lower = text.lower() if text else ""
    
    # Simple rule-based mock QA
    if "revenue" in q_lower or "sales" in q_lower or "financial" in q_lower or "grow" in q_lower:
        if "q1" in text_lower:
            return "Based on the Q1 summary, overall revenue increased by 14.5% year-on-year, driven by regional portfolio expansion. Additionally, efficiency programs saved about $4.2M."
        else:
            return "Based on the text, there are mentions of strategic financial milestones, cost-efficiency measures, and potential resource reallocation to support growth."
            
    if "risk" in q_lower or "warning" in q_lower or "danger" in q_lower:
        return "The document notes potential risks regarding supply chain bottlenecks in primary manufacturing hubs and fluctuations in exchange rates impacting overseas margins."
        
    if "action" in q_lower or "next step" in q_lower or "todo" in q_lower:
        return "Key action items identified include forming a governance board, auditing existing databases for preparation, and shifting approximately 15% of traditional marketing budgets to performance-based digital channels."

    if "ai" in q_lower or "artificial intelligence" in q_lower or "model" in q_lower:
        return "The document describes AI implementation strategies, noting that rapid integration of models yields about a 30% increase in operational throughput, provided data quality and governance are properly managed."

    # General fallback
    keywords = extract_keywords(text, top_n=5)
    kw_str = ", ".join(keywords) if keywords else "the document's topic"
    return f"This is an offline demo answer. The document discusses topics related to **{kw_str}**. To ask specific questions live, please connect your Pollinations AI API key in the `.env` file."

def query_pdf_data(text: str, user_question: str, history: list = None, api_key: str = None, is_demo: bool = False) -> str:
    """
    Answers user questions about the PDF document using Pollinations AI or a smart fallback.
    """
    if not api_key:
        api_key = load_env_api_key()
        
    use_mock = is_demo or not api_key
    
    if use_mock:
        return get_mock_chat_response(text, user_question)
        
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://gen.pollinations.ai/v1",
            api_key=api_key
        )
        
        # Clean text
        clean_text = re.sub(r'\s+', ' ', text).strip()
        context = clean_text[:6000] # Limit context size
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful AI Document Assistant. You are given the text of a PDF document. "
                    "Answer the user's question accurately based ONLY on the provided document context. "
                    "If the answer cannot be found in the document, politely say so. Do not make up facts. "
                    "Keep your response concise and structured."
                )
            },
            {
                "role": "system",
                "content": f"DOCUMENT CONTENT:\n{context}"
            }
        ]
        
        # Append history if provided
        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
                
        # Append current question
        messages.append({"role": "user", "content": user_question})
        
        response = client.chat.completions.create(
            model="openai",
            messages=messages,
            temperature=0.5
        )
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error connecting to Pollinations AI: {str(e)}. (Fallback to offline demo mode answer: {get_mock_chat_response(text, user_question)})"

