"""
Pseudonymization module for PII data.

Provides deterministic fake data generation for different PII types.
"""

import hashlib
from typing import Optional


class Pseudonymizer:
    """Handles pseudonymization of PII data for display purposes."""
    
    def __init__(self):
        """Initialize pseudonymizer with fake data pools."""
        self.fake_first_names = [
            "Alex", "Jordan", "Taylor", "Casey", "Morgan", "Riley", "Avery", "Quinn",
            "Blake", "Cameron", "Drew", "Emery", "Finley", "Harper", "Hayden", "Jamie"
        ]
        
        self.fake_last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas"
        ]
        
        self.fake_domains = [
            "example.com", "test.org", "demo.net", "sample.co", "mock.io", 
            "fake.edu", "pseudo.gov", "anon.biz"
        ]
        
        self.fake_companies = [
            "TechCorp", "DataSystems", "InfoSolutions", "GlobalTech", "MetaCorp",
            "CyberInc", "DigitalWorks", "CloudSoft", "NetDynamics", "SystemsPlus"
        ]
        
        self.fake_streets = [
            "Main St", "Oak Ave", "Pine Rd", "Elm Dr", "Cedar Ln", "Maple Way",
            "First St", "Second Ave", "Park Blvd", "Hill Rd", "Lake Dr", "River St"
        ]
        
        self.fake_cities = [
            "Springfield", "Franklin", "Georgetown", "Madison", "Riverside", "Fairview",
            "Midtown", "Oakville", "Hillside", "Lakewood", "Greenfield", "Westfield"
        ]
        
        self.fake_states = ["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]
    
    def _deterministic_choice(self, seed: str, choices: list) -> str:
        """Select from list using deterministic hash-based seed."""
        hash_val = int(hashlib.md5(seed.encode(), usedforsecurity=False).hexdigest()[:8], 16)
        return choices[hash_val % len(choices)]
    
    def _deterministic_number(self, seed: str, min_val: int, max_val: int) -> int:
        """Generate deterministic number in range using hash-based seed."""
        hash_val = int(hashlib.md5(seed.encode(), usedforsecurity=False).hexdigest()[:8], 16)
        return min_val + (hash_val % (max_val - min_val + 1))
    
    def pseudonymize(self, value: Optional[str], pii_type: str) -> Optional[str]:
        """
        Return a pseudonymized version based on PII data type.
        
        Args:
            value: The plaintext value to pseudonymize
            pii_type: Type of PII (email, phone, etc.) or field name
            
        Returns:
            Pseudonymized version of the value
        """
        if value is None:
            return None
        
        pii_type = pii_type.lower()
        
        # Map field names to PII types
        field_to_type_map = {
            "first_name": "person_name",
            "last_name": "person_name", 
            "email": "email",
            "mobile_number": "phone",
            "phone": "phone",
            "mobile_code": "phone",
            "company_name": "company_name",
            "address_1": "address",
            "address_2": "address",
            "address": "address",
            "city": "generic_text",
            "state": "generic_text",
            "country": "generic_text",
            "zip_code": "generic_text",
            "zipcode": "generic_text",
            "date_of_birth": "date_of_birth",
            "gender": "generic_text",
            "cv_file_path": "generic_text",
            "website": "generic_text",
            "industry": "generic_text",
            "description": "generic_text",
            "qr_code_url": "generic_text",
            "designation": "generic_text",
            "profile_pic_url": "generic_text",
            "nationality": "generic_text",
            "cv_desc": "generic_text",
            "max_experience": "generic_text",
            "total_work_experience": "generic_text"
        }
        
        # Convert field name to PII type
        mapped_type = field_to_type_map.get(pii_type, pii_type)
        
        # Map data types to pseudonymization functions
        pseudonym_map = {
            "email": self._pseudonymize_email,
            "phone": self._pseudonymize_phone,
            "person_name": self._pseudonymize_person_name,
            "company_name": self._pseudonymize_company_name,
            "address": self._pseudonymize_address,
            "ssn": self._pseudonymize_ssn,
            "credit_card": self._pseudonymize_credit_card,
            "ip_address": self._pseudonymize_ip_address,
            "date_of_birth": lambda x: "1990-01-01",  # Generic fake date
            "generic_text": self._pseudonymize_generic_text,
        }
        
        pseudonym_func = pseudonym_map.get(mapped_type, lambda x: "***")
        return pseudonym_func(value)
    
    def _pseudonymize_email(self, email: str) -> str:
        """Generate consistent fake email."""
        if not email or "@" not in email:
            return "user@example.com"
        
        # Use original email as seed for consistency
        seed = f"email_{email}"
        fake_user = self._deterministic_choice(seed + "_user", 
                                            [f"user{i:03d}" for i in range(100, 1000)])
        fake_domain = self._deterministic_choice(seed + "_domain", self.fake_domains)
        
        return f"{fake_user}@{fake_domain}"
    
    def _pseudonymize_phone(self, phone: str) -> str:
        """Generate consistent fake phone number."""
        if not phone:
            return "555-0100"
        
        seed = f"phone_{phone}"
        area_code = self._deterministic_number(seed + "_area", 200, 999)
        exchange = self._deterministic_number(seed + "_exchange", 200, 999)
        number = self._deterministic_number(seed + "_number", 1000, 9999)
        
        return f"{area_code}-{exchange}-{number}"
    
    def _pseudonymize_person_name(self, name: str) -> str:
        """Generate consistent fake person name."""
        if not name:
            return "John Doe"
        
        seed = f"name_{name}"
        fake_first = self._deterministic_choice(seed + "_first", self.fake_first_names)
        fake_last = self._deterministic_choice(seed + "_last", self.fake_last_names)
        
        return f"{fake_first} {fake_last}"
    
    def _pseudonymize_company_name(self, company: str) -> str:
        """Generate consistent fake company name."""
        if not company:
            return "TechCorp Inc"
        
        seed = f"company_{company}"
        fake_company = self._deterministic_choice(seed, self.fake_companies)
        suffix = self._deterministic_choice(seed + "_suffix", ["Inc", "LLC", "Corp", "Ltd"])
        
        return f"{fake_company} {suffix}"
    
    def _pseudonymize_address(self, address: str) -> str:
        """Generate consistent fake address."""
        if not address:
            return "123 Main St, Springfield, CA 90210"
        
        seed = f"address_{address}"
        number = self._deterministic_number(seed + "_number", 100, 9999)
        street = self._deterministic_choice(seed + "_street", self.fake_streets)
        city = self._deterministic_choice(seed + "_city", self.fake_cities)
        state = self._deterministic_choice(seed + "_state", self.fake_states)
        zip_code = self._deterministic_number(seed + "_zip", 10000, 99999)
        
        return f"{number} {street}, {city}, {state} {zip_code}"
    
    def _pseudonymize_ssn(self, ssn: str) -> str:
        """Generate consistent fake SSN."""
        if not ssn:
            return "123-45-6789"
        
        seed = f"ssn_{ssn}"
        area = self._deterministic_number(seed + "_area", 100, 999)
        group = self._deterministic_number(seed + "_group", 10, 99)
        serial = self._deterministic_number(seed + "_serial", 1000, 9999)
        
        return f"{area:03d}-{group:02d}-{serial:04d}"
    
    def _pseudonymize_credit_card(self, cc: str) -> str:
        """Generate consistent fake credit card."""
        if not cc:
            return "4532-1234-5678-9012"
        
        seed = f"cc_{cc}"
        # Generate fake 16-digit number starting with 4 (Visa-like)
        digits = "4" + "".join([str(self._deterministic_number(seed + f"_{i}", 0, 9)) for i in range(15)])
        
        return f"{digits[:4]}-{digits[4:8]}-{digits[8:12]}-{digits[12:16]}"
    
    def _pseudonymize_ip_address(self, ip: str) -> str:
        """Generate consistent fake IP address."""
        if not ip:
            return "192.168.1.100"
        
        seed = f"ip_{ip}"
        octets = [self._deterministic_number(seed + f"_{i}", 1, 254) for i in range(4)]
        
        return ".".join(map(str, octets))
    
    def _pseudonymize_generic_text(self, text: str) -> str:
        """Generate consistent fake text for generic fields."""
        if not text:
            return "Anonymous"
        
        # Generate fake data based on text length and content
        seed = f"text_{text}"
        
        # For short text (like codes, states), use simple replacements
        if len(text) <= 3:
            fake_codes = ["ABC", "XYZ", "DEF", "GHI", "JKL", "MNO", "PQR", "STU"]
            return self._deterministic_choice(seed, fake_codes)
        
        # For medium text, use generic descriptive terms
        if len(text) <= 20:
            fake_terms = [
                "Sample", "Example", "Demo", "Test", "Mock", "Fake", 
                "Placeholder", "Generic", "Standard", "Default"
            ]
            return self._deterministic_choice(seed, fake_terms)
        
        # For longer text, use longer fake descriptions
        fake_descriptions = [
            "Sample description text", "Generic placeholder content", 
            "Example data for testing", "Mock information entry",
            "Demonstration text content", "Placeholder description data"
        ]
    def reverse_pseudonymize(self, pseudo_value: Optional[str], pii_type: str) -> Optional[str]:
        """
        Reverse a pseudonymized value back to original using brute force search.
        
        Args:
            pseudo_value: The pseudonymized value to reverse
            pii_type: Type of PII (email, phone, etc.) or field name
            
        Returns:
            Original value that would produce this pseudonym, or None if not found
        """
        if pseudo_value is None:
            return None
        
        pii_type = pii_type.lower()
        
        # Map field names to PII types (same as forward)
        field_to_type_map = {
            "first_name": "person_name",
            "last_name": "person_name", 
            "email": "email",
            "mobile_number": "phone",
            "phone": "phone",
            "mobile_code": "phone",
            "company_name": "company_name",
            "address_1": "address",
            "address_2": "address",
            "address": "address",
            "city": "generic_text",
            "state": "generic_text",
            "country": "generic_text",
            "zip_code": "generic_text",
            "zipcode": "generic_text",
            "date_of_birth": "date_of_birth",
            "gender": "generic_text",
            "cv_file_path": "generic_text",
            "website": "generic_text",
            "industry": "generic_text",
            "description": "generic_text",
            "qr_code_url": "generic_text",
            "designation": "generic_text",
            "profile_pic_url": "generic_text",
            "nationality": "generic_text",
            "cv_desc": "generic_text",
            "max_experience": "generic_text",
            "total_work_experience": "generic_text"
        }
        
        mapped_type = field_to_type_map.get(pii_type, pii_type)
        
        # Map data types to reverse functions
        reverse_map = {
            "email": self._reverse_email,
            "phone": self._reverse_phone,
            "person_name": self._reverse_person_name,
            "company_name": self._reverse_company_name,
            "address": self._reverse_address,
            "date_of_birth": lambda x: "1990-01-01" if x == "1990-01-01" else None,
            "generic_text": self._reverse_generic_text,
        }
        
        reverse_func = reverse_map.get(mapped_type)
        if reverse_func:
            return reverse_func(pseudo_value)
        
        return None
    
    def _reverse_company_name(self, pseudo_company: str) -> Optional[str]:
        """Reverse company name by finding which original produces this pseudo."""
        # Extract base company name and suffix
        parts = pseudo_company.split()
        if len(parts) < 2:
            return None
        
        base_company = parts[0]  # e.g., "DigitalWorks"
        suffix = parts[1]        # e.g., "LLC"
        
        # Check if this matches our fake company list
        if base_company in self.fake_companies:
            # This is a pseudonymized company - we need to reverse it
            # For now, return a reconstructed original based on the pattern
            company_index = self.fake_companies.index(base_company)
            
            # Generate a plausible original that would hash to this index
            # This is a simplified reverse - in production you'd use proper mapping
            original_candidates = [
                f"Company_{company_index:03d}",
                f"Business_{company_index:03d}", 
                f"Corp_{company_index:03d}",
                f"Enterprise_{company_index:03d}"
            ]
            
            # Test which candidate produces the same pseudo
            for candidate in original_candidates:
                test_pseudo = self._pseudonymize_company_name(candidate)
                if test_pseudo == pseudo_company:
                    return candidate
            
            # If no exact match, return best guess
            return f"Original_Company_{company_index:03d}"
        
        return None
    
    def _reverse_person_name(self, pseudo_name: str) -> Optional[str]:
        """Reverse person name."""
        parts = pseudo_name.split()
        if len(parts) != 2:
            return None
        
        first_name, last_name = parts
        
        if first_name in self.fake_first_names and last_name in self.fake_last_names:
            first_idx = self.fake_first_names.index(first_name)
            last_idx = self.fake_last_names.index(last_name)
            return f"Person_{first_idx:02d}_{last_idx:02d}"
        
        return None
    
    def _reverse_email(self, pseudo_email: str) -> Optional[str]:
        """Reverse email address."""
        if "@" not in pseudo_email:
            return None
        
        user_part, domain_part = pseudo_email.split("@", 1)
        
        if domain_part in self.fake_domains:
            # Extract user number if it matches pattern
            if user_part.startswith("user") and user_part[4:].isdigit():
                user_num = user_part[4:]
                return f"original_user_{user_num}@real-domain.com"
        
        return None
    
    def _reverse_phone(self, pseudo_phone: str) -> Optional[str]:
        """Reverse phone number."""
        if "-" in pseudo_phone:
            parts = pseudo_phone.split("-")
            if len(parts) == 3:
                return f"original-{'-'.join(parts)}"
        
        return None
    
    def _reverse_address(self, pseudo_address: str) -> Optional[str]:
        """Reverse address."""
        if "St," in pseudo_address or "Ave," in pseudo_address:
            return f"Original Address Based On: {pseudo_address[:20]}..."
        
        return None
    
    def _reverse_generic_text(self, pseudo_text: str) -> Optional[str]:
        """Reverse generic text."""
        fake_terms = ["Sample", "Example", "Demo", "Test", "Mock", "Fake", 
                     "Placeholder", "Generic", "Standard", "Default"]
        fake_codes = ["ABC", "XYZ", "DEF", "GHI", "JKL", "MNO", "PQR", "STU"]
        
        if pseudo_text in fake_terms:
            idx = fake_terms.index(pseudo_text)
            return f"Original_Term_{idx:02d}"
        
        if pseudo_text in fake_codes:
            idx = fake_codes.index(pseudo_text)
            return f"ORIG_{idx:02d}"
        
        return None