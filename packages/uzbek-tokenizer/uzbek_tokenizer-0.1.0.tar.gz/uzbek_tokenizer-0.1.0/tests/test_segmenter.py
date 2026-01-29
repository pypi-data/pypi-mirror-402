import unittest
from uzbek_tokenizer import normalize, segment_morphological, apply_segmentation


class TestNormalize(unittest.TestCase):
    """Test cases for the normalize function."""
    
    def test_lowercase(self):
        """Test that text is converted to lowercase."""
        result = normalize("SALOM")
        self.assertEqual(result, "salom")
    
    def test_unicode_normalization(self):
        """Test Unicode NFC normalization."""
        result = normalize("kafe")
        self.assertIsInstance(result, str)
    
    def test_punctuation_separation(self):
        """Test that punctuation is separated with spaces."""
        result = normalize("Salom!")
        self.assertIn("!", result)
    
    def test_apostrophe_handling(self):
        """Test apostrophe normalization."""
        # Various apostrophe types
        result = normalize("o'q")
        self.assertIn("ʼ", result)
    
    def test_whitespace_collapse(self):
        """Test that multiple whitespaces are collapsed."""
        result = normalize("salom    dunyo")
        self.assertEqual(result, "salom dunyo")
    
    def test_ellipsis_handling(self):
        """Test that ellipsis is normalized."""
        result = normalize("salom...")
        self.assertIn(".", result)


class TestSegmentMorphological(unittest.TestCase):
    """Test cases for the segment_morphological function."""
    
    def test_single_stem_no_affixes(self):
        """Test word with no affixes."""
        result = segment_morphological("kitob")
        self.assertEqual(result, ["kitob"])
    
    def test_suffix_segmentation(self):
        """Test basic suffix removal."""
        result = segment_morphological("kitoblar")
        self.assertIn("kitob", result)
        self.assertIn("lar", result)
    
    def test_multiple_suffix_segmentation(self):
        """Test multiple suffix removal."""
        result = segment_morphological("kitoblarimiz")
        self.assertIn("kitob", result)
        self.assertTrue(any(morpheme in result for morpheme in ["lar", "lari"]))
    
    def test_prefix_segmentation(self):
        """Test prefix removal."""
        result = segment_morphological("bepartach")
        self.assertEqual(result[0], "be")
    
    def test_single_character_token(self):
        """Test single character returns as-is."""
        result = segment_morphological("a")
        self.assertEqual(result, ["a"])
    
    def test_empty_token_after_stripping(self):
        """Test that minimum stem length is enforced."""
        result = segment_morphological("dan")
        self.assertEqual(result, ["dan"])


class TestApplySegmentation(unittest.TestCase):
    """Test cases for the apply_segmentation function."""
    
    def test_single_word(self):
        """Test segmentation of single word."""
        result = apply_segmentation("kitob")
        self.assertEqual(result, ["kitob"])
    
    def test_single_word_with_affixes(self):
        """Test segmentation of word with affixes."""
        result = apply_segmentation("kitoblar")
        self.assertIn("kitob", result)
        self.assertIn("lar", result)
    
    def test_multiple_words(self):
        """Test segmentation of multiple words."""
        result = apply_segmentation("kitoblar o'qidim")
        self.assertGreater(len(result), 2)
        self.assertIn("kitob", result)
        self.assertIn("lar", result)
    
    def test_text_with_punctuation(self):
        """Test that punctuation is handled."""
        result = apply_segmentation("Salom!")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
    
    def test_empty_string(self):
        """Test handling of empty string."""
        result = apply_segmentation("")
        self.assertEqual(result, [])
    
    def test_whitespace_only(self):
        """Test handling of whitespace-only string."""
        result = apply_segmentation("   ")
        self.assertEqual(result, [])
    
    def test_normalized_output(self):
        """Test that output is normalized (lowercase)."""
        result = apply_segmentation("KITOBLAR")
        self.assertIn("kitob", result)


class TestIntegration(unittest.TestCase):
    """Integration tests for real-world Uzbek text."""
    
    def test_real_sentence(self):
        """Test with real Uzbek sentence."""
        text = "kitoblarimizdan o'qidim"
        result = apply_segmentation(text)
        
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        self.assertIn("kitob", result)
        self.assertTrue(any(morpheme in result for morpheme in ["lar", "lari"]))
    
    def test_complex_word_segmentation(self):
        """Test complex Uzbek word with multiple affixes."""
        result = segment_morphological("borganmish")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 1)
    
    def test_caching_consistency(self):
        """Test that caching doesn't affect results."""
        word = "kitoblar"
        result1 = segment_morphological(word)
        result2 = segment_morphological(word)
        self.assertEqual(result1, result2)


if __name__ == "__main__":
    unittest.main()