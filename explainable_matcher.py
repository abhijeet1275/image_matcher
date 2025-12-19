import torch
import open_clip
from typing import List, Dict
import re

class ExplainableImageMatcher:
    """
    Hybrid explainable image-text matching.
    Uses original CLIP cosine similarity as the final score,
    but provides detailed explanations via feature decomposition.
    """
    
    def __init__(self, model, tokenizer, preprocess, device):
        self.model = model
        self.tokenizer = tokenizer
        self.preprocess = preprocess
        self.device = device
        
        # Similarity thresholds for categorization
        self.STRONG_THRESHOLD = 0.45
        self.PARTIAL_THRESHOLD = 0.25
        
    def decompose_prompt(self, prompt: str) -> List[Dict[str, any]]:
        """
        Decompose a long interior design prompt into semantic units.
        Returns list of dicts with keys: 'feature', 'category'
        """
        features = []
        
        # Pattern-based extraction for common interior design features
        style_patterns = [
            r'(modern|contemporary|traditional|rustic|industrial|minimalist|scandinavian|farmhouse|elegant|luxury|cozy)[\s\w]*(?:kitchen|interior|design|style)',
            r'(open\s+concept|spacious|compact|bright)',
        ]
        
        layout_patterns = [
            r'([ULI]-shaped|galley|peninsula|island)[\s\w]*(?:kitchen|layout)',
            r'(breakfast\s+counter|dining\s+area|bar\s+seating|kitchen\s+island)',
        ]
        
        material_patterns = [
            r'(sage\s+green|white|black|grey|gray|navy|blue|beige|cream|brown|wooden|marble|granite|quartz|stone|stainless\s+steel)[\s\w]*(?:cabinets?|countertops?|backsplash|flooring|walls?)',
            r'(upper|lower)[\s\w]*cabinets?.*?(glass|wooden|open|closed|shaker|flat-panel)',
        ]
        
        lighting_patterns = [
            r'(warm|cool|natural|LED|pendant|recessed|track|ambient)[\s\w]*lighting',
            r'(chandelier|pendant\s+lights?|under-cabinet\s+lighting|ceiling\s+lights?)',
        ]
        
        fixture_patterns = [
            r'(stainless\s+steel|black|white|matte)[\s\w]*(?:appliances?|refrigerator|oven|stove|range|sink|faucet)',
            r'(farmhouse|undermount|double|single)[\s\w]*sink',
        ]
        
        photo_patterns = [
            r'(wide-angle|close-up|panoramic|aerial)[\s\w]*(?:shot|view|photo|perspective)',
            r'(interior\s+photography|architectural\s+shot)',
        ]
        
        pattern_configs = [
            (style_patterns, 'style'),
            (layout_patterns, 'layout'),
            (material_patterns, 'material'),
            (lighting_patterns, 'lighting'),
            (fixture_patterns, 'fixtures'),
            (photo_patterns, 'photography'),
        ]
        
        prompt_lower = prompt.lower()
        seen_features = set()
        
        for patterns, category in pattern_configs:
            for pattern in patterns:
                matches = re.finditer(pattern, prompt_lower, re.IGNORECASE)
                for match in matches:
                    feature_text = match.group(0).strip()
                    if feature_text not in seen_features and len(feature_text) > 5:
                        features.append({
                            'feature': feature_text,
                            'category': category
                        })
                        seen_features.add(feature_text)
        
        # If no patterns matched, create general semantic chunks
        if not features:
            chunks = re.split(r'[,.]', prompt)
            for chunk in chunks:
                chunk = chunk.strip()
                if len(chunk) > 10:
                    features.append({
                        'feature': chunk,
                        'category': 'general'
                    })
        
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
        
        # Decompose prompt for explanation
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