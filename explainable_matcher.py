import torch
import open_clip
from typing import List, Dict
import os
from openai import OpenAI

class ExplainableImageMatcher:
    """
    Hybrid explainable image-text matching.
    Uses original CLIP cosine similarity as the final score,
    but provides detailed explanations via feature decomposition using GPT.
    """
    
    def __init__(self, model, tokenizer, preprocess, device):
        self.model = model
        self.tokenizer = tokenizer
        self.preprocess = preprocess
        self.device = device
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("⚠️  WARNING: OPENAI_API_KEY not found. Feature extraction will use fallback method.")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
        
        # Similarity thresholds for categorization
        self.STRONG_THRESHOLD = 0.45
        self.PARTIAL_THRESHOLD = 0.25
        
    def decompose_prompt(self, prompt: str) -> List[Dict[str, any]]:
        """
        Use GPT to decompose a prompt into semantic features.
        Returns list of dicts with keys: 'feature', 'category'
        """
        if not self.client:
            return self._fallback_decomposition(prompt)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at analyzing interior design prompts. 
Extract key visual features from the given prompt and categorize them.

Categories:
- style: overall design style (modern, rustic, minimalist, etc.)
- layout: spatial arrangement (open concept, island, L-shaped, etc.)
- material: materials and colors (wood, marble, sage green, etc.)
- lighting: lighting features (pendant lights, natural light, LED, etc.)
- fixtures: appliances and fixtures (stainless steel appliances, farmhouse sink, etc.)
- photography: photo characteristics (wide-angle, close-up, etc.)
- general: anything else important

Return ONLY a JSON array of objects with 'feature' and 'category' keys.
Each feature should be a short, specific phrase (3-8 words).
Example: [{"feature": "modern minimalist kitchen", "category": "style"}, {"feature": "sage green lower cabinets", "category": "material"}]"""
                    },
                    {
                        "role": "user",
                        "content": f"Extract visual features from this prompt: {prompt}"
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse GPT response
            import json
            features_text = response.choices[0].message.content.strip()
            
            # Clean up response if it has markdown code blocks
            if features_text.startswith('```'):
                features_text = features_text.split('```')[1]
                if features_text.startswith('json'):
                    features_text = features_text[4:]
                features_text = features_text.strip()
            
            features = json.loads(features_text)
            
            print(f"✓ GPT extracted {len(features)} features from prompt")
            return features
            
        except Exception as e:
            print(f"⚠️  GPT extraction failed: {e}. Using fallback method.")
            return self._fallback_decomposition(prompt)
    
    def _fallback_decomposition(self, prompt: str) -> List[Dict[str, any]]:
        """
        Simple fallback method if GPT is unavailable.
        Splits prompt into chunks by commas and conjunctions.
        """
        import re
        
        features = []
        
        # Split by common delimiters
        chunks = re.split(r',|\s+and\s+|\s+with\s+', prompt)
        
        for chunk in chunks:
            chunk = chunk.strip()
            if len(chunk) > 5:  # Ignore very short chunks
                # Try to categorize based on keywords
                chunk_lower = chunk.lower()
                
                if any(word in chunk_lower for word in ['modern', 'rustic', 'minimalist', 'contemporary', 'traditional', 'elegant']):
                    category = 'style'
                elif any(word in chunk_lower for word in ['cabinet', 'countertop', 'backsplash', 'wood', 'marble', 'granite', 'stone']):
                    category = 'material'
                elif any(word in chunk_lower for word in ['light', 'lighting', 'pendant', 'chandelier', 'led']):
                    category = 'lighting'
                elif any(word in chunk_lower for word in ['island', 'layout', 'open concept', 'shaped']):
                    category = 'layout'
                elif any(word in chunk_lower for word in ['appliance', 'sink', 'faucet', 'oven', 'refrigerator']):
                    category = 'fixtures'
                else:
                    category = 'general'
                
                features.append({
                    'feature': chunk,
                    'category': category
                })
        
        print(f"✓ Fallback method extracted {len(features)} features")
        return features
    
    def compute_feature_similarities(self, image_embedding: torch.Tensor, 
                                     features: List[Dict]) -> List[Dict]:
        """
        Compute cosine similarity between image and each text feature.
        This is for explanation only - not used for final scoring.
        """
        if not features:
            return []
            
        feature_texts = [f['feature'] for f in features]
        text_tokens = self.tokenizer(feature_texts).to(self.device)
        
        with torch.no_grad():
            text_embeddings = self.model.encode_text(text_tokens)
            text_embeddings /= text_embeddings.norm(dim=-1, keepdim=True)
            
            similarities = (image_embedding @ text_embeddings.T).squeeze(0)
        
        for i, feature in enumerate(features):
            sim_value = similarities[i].item()
            feature['similarity'] = sim_value
            
            if sim_value >= self.STRONG_THRESHOLD:
                feature['status'] = 'strong'
            elif sim_value >= self.PARTIAL_THRESHOLD:
                feature['status'] = 'partial'
            else:
                feature['status'] = 'weak'
        
        return features
    
    def generate_explanation(self, features: List[Dict], original_score: float) -> str:
        """
        Generate explanation based on feature breakdown.
        Explains WHY the original cosine similarity is what it is.
        """
        strong = [f for f in features if f['status'] == 'strong']
        partial = [f for f in features if f['status'] == 'partial']
        weak = [f for f in features if f['status'] == 'weak']
        
        explanation_parts = []
        
        # Overall assessment based on original score
        if original_score >= 45:
            explanation_parts.append(f"Overall Match Score: {original_score:.2f}% (Strong Match)")
            explanation_parts.append("\nThis high score indicates the image aligns well with the prompt.")
        elif original_score >= 25:
            explanation_parts.append(f"Overall Match Score: {original_score:.2f}% (Moderate Match)")
            explanation_parts.append("\nThis moderate score suggests some alignment with mixed results.")
        else:
            explanation_parts.append(f"Overall Match Score: {original_score:.2f}% (Weak Match)")
            explanation_parts.append("\nThis low score indicates significant misalignment with the prompt.")
        
        # Explain what's contributing positively
        if strong:
            explanation_parts.append("\n\n✓ Strong Matches (Contributing to the score):")
            for f in sorted(strong, key=lambda x: x['similarity'], reverse=True)[:3]:
                explanation_parts.append(
                    f"  • '{f['feature']}' is clearly present "
                    f"(feature similarity: {f['similarity']:.2f})"
                )
        
        # Explain partial matches
        if partial:
            explanation_parts.append("\n\n◐ Partial Matches (Somewhat contributing):")
            for f in sorted(partial, key=lambda x: x['similarity'], reverse=True)[:3]:
                explanation_parts.append(
                    f"  • '{f['feature']}' is partially visible "
                    f"(feature similarity: {f['similarity']:.2f})"
                )
        
        # Explain what's missing or weak
        if weak:
            explanation_parts.append("\n\n✗ Weak/Missing Features (Lowering the score):")
            for f in sorted(weak, key=lambda x: x['similarity'])[:3]:
                explanation_parts.append(
                    f"  • '{f['feature']}' is not clearly visible "
                    f"(feature similarity: {f['similarity']:.2f})"
                )
        
        # Summary
        explanation_parts.append(f"\n\nSummary: Out of {len(features)} identified features, ")
        explanation_parts.append(f"{len(strong)} are strong matches, ")
        explanation_parts.append(f"{len(partial)} are partial matches, and ")
        explanation_parts.append(f"{len(weak)} are weak/missing.")
        
        if original_score >= 45:
            explanation_parts.append(" This explains the high overall match score.")
        elif original_score >= 25:
            explanation_parts.append(" The mixed results explain the moderate overall score.")
        else:
            explanation_parts.append(" The lack of strong matches explains the low overall score.")
        
        return "".join(explanation_parts)
    
    def explain_match(self, image, prompt: str) -> Dict:
        """
        Complete explainable matching pipeline.
        Returns original CLIP similarity with detailed explanation.
        """
        # Encode image
        if not isinstance(image, torch.Tensor):
            image = self.preprocess(image).unsqueeze(0)
        image = image.to(self.device)
        
        with torch.no_grad():
            image_embedding = self.model.encode_image(image)
            image_embedding /= image_embedding.norm(dim=-1, keepdim=True)
            
            # Get ORIGINAL cosine similarity with full prompt
            full_prompt_tokens = self.tokenizer([prompt]).to(self.device)
            text_embedding = self.model.encode_text(full_prompt_tokens)
            text_embedding /= text_embedding.norm(dim=-1, keepdim=True)
            
            # This is the ORIGINAL score we keep
            original_similarity = (image_embedding @ text_embedding.T).squeeze()
            original_score = original_similarity.item() * 100
        
        # Decompose prompt using GPT
        features = self.decompose_prompt(prompt)
        
        # Compute feature similarities (for explanation only)
        features = self.compute_feature_similarities(image_embedding, features)
        
        # Generate explanation
        explanation_text = self.generate_explanation(features, original_score)
        
        return {
            'final_score': round(original_score, 2),
            'feature_breakdown': [
                {
                    'feature': f['feature'],
                    'similarity': round(f['similarity'], 3),
                    'status': f['status'],
                    'category': f['category']
                }
                for f in features
            ],
            'explanation_text': explanation_text
        }