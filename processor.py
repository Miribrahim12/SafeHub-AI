import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account
import os
import json
import requests
import re

class ThreatAnalyzer:
    def __init__(self):
        # 1. Sənin qeyd etdiyin mütləq fayl yolu
        self.key_path = "/home/huseynlimiribrahim18/safehub-project/key.json"
        
        # Obyekti mütləq None olaraq başladırıq
        self.model = None

        try:
            # Faylın mövcudluğunu yoxlayırıq
            if not os.path.exists(self.key_path):
                # Əgər o yolda yoxdursa, cari qovluğa bax
                self.key_path = "key.json"
                if not os.path.exists(self.key_path):
                    raise FileNotFoundError(f"Açar faylı tapılmadı: {self.key_path}")

            # 2. Autentifikasiya
            self.credentials = service_account.Credentials.from_service_account_file(self.key_path)
            
            # 3. Vertex AI Başlatma
            vertexai.init(
                project="safehub-ai", 
                location="europe-west1", 
                credentials=self.credentials
            )
            
            # 4. Stabil model (404 xətası verməyən ən etibarlı versiya)
            self.model = GenerativeModel("gemini-2.5-flash")
            print("--- [SUCCESS] Vertex AI aktivdir ---")
            
        except Exception as e:
            print(f"--- [KRİTİK XƏTA] Başlatma zamanı: {e} ---")

    def expand_url(self, message):
        """Linkləri analiz edib yönləndirmələri tapır"""
        urls = re.findall(r'(https?://\S+)', message)
        expanded_info = ""
        for url in urls:
            try:
                resp = requests.head(url, allow_redirects=True, timeout=5)
                expanded_info += f"\n[Link Analizi]: {url} -> {resp.url} ünvanına yönlənir."
            except Exception:
                expanded_info += f"\n[Link Analizi]: {url} (Yoxlanıla bilmədi)"
        return expanded_info

    def analyze_message(self, message):
        # 5. Sistem hazır deyilsə, 0 risk qaytarırıq (İstifadəçini qorxutmuruq)
        if self.model is None:
            return {
                "risk_score": 0,
                "threat_type": "Sistem Hazır Deyil",
                "is_threat": "No",
                "reason": "AI Modeli yüklənməyib. Zəhmət olmasa terminalı yoxlayın.",
                "action_plan": "Serveri terminalda yenidən başladın.",
                "confidence": "0%",
                "technical_details": "Model object is None"
            }

        link_extra_info = self.expand_url(message)
        
        # 6. Professional Prompt (Frontend üçün mütləq format)
        prompt = f"""
        Sən kiber-təhlükəsizlik AI-san. Aşağıdakı mesajı Azərbaycan kontekstində analiz et.
        Mesaj: "{message}"
        {link_extra_info}
        
        Cavabı YALNIZ bu JSON formatında qaytar:
        {{
            "risk_score": 0-10 arası rəqəm,
            "threat_type": "Hücum növü",
            "is_threat": "Yes/No",
            "reason": "Azərbaycan dilində qısa izah",
            "action_plan": "3 konkret məsləhət",
            "confidence": "95%",
            "technical_details": "Texniki qeyd"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # JSON-u təmizləmək üçün regex (Hər ehtimala qarşı)
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                
                # Risk score-un rəqəm olmasını təmin edirik (Frontend-dəki Gauge üçün)
                try:
                    result["risk_score"] = int(result.get("risk_score", 0))
                except:
                    result["risk_score"] = 0
                
                # Undefined xətalarını bitirmək üçün default dəyərlər
                required_keys = ["threat_type", "is_threat", "reason", "action_plan", "confidence", "technical_details"]
                for key in required_keys:
                    if key not in result:
                        result[key] = "Analiz məlumatı yoxdur."
                
                return result
            else:
                raise ValueError("JSON tapılmadı")
                
        except Exception as e:
            return {
                "risk_score": 0,
                "threat_type": "Analiz Xətası",
                "is_threat": "No",
                "reason": f"Sistem xətası: {str(e)}",
                "action_plan": "Bilinməyən linklərə klikləməyin.",
                "confidence": "0%",
                "technical_details": "Fallback active"
            }
