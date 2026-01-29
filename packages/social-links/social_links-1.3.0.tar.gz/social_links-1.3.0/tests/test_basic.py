import pytest
from sociallinks import detect_platform, is_valid, sanitize, list_platforms
from sociallinks.core import SocialLinks
from sociallinks.exceptions import (
    PlatformNotFoundError,
    URLMismatchError,
)


class TestModuleLevelDetectPlatform:
    """Test detect_platform() module-level function"""

    def test_detect_linkedin_personal(self):
        """Test detecting LinkedIn personal profile"""
        assert detect_platform("https://www.linkedin.com/in/johndoe/") == "linkedin"
        assert detect_platform("http://linkedin.com/in/johndoe") == "linkedin"
        assert detect_platform("https://linkedin.com/in/jane-smith") == "linkedin"

    def test_detect_linkedin_company(self):
        """Test detecting LinkedIn company profile"""
        assert detect_platform("https://www.linkedin.com/company/acme/") == "linkedin"
        assert detect_platform("http://linkedin.com/company/techcorp") == "linkedin"

    def test_detect_facebook(self):
        """Test detecting Facebook platform"""
        assert detect_platform("https://www.facebook.com/johndoe/") == "facebook"
        assert detect_platform("http://facebook.com/janedoe") == "facebook"

    def test_detect_github(self):
        """Test detecting GitHub platform"""
        assert detect_platform("https://github.com/username") == "github"
        assert detect_platform("https://www.github.com/username") == "github"

    def test_detect_x(self):
        """Test detecting X (Twitter) platform"""
        assert detect_platform("https://x.com/username") == "x"
        assert detect_platform("https://twitter.com/username") == "x"

    def test_detect_instagram(self):
        """Test detecting Instagram platform"""
        assert detect_platform("https://instagram.com/username") == "instagram"
        assert detect_platform("https://www.instagram.com/username") == "instagram"

    def test_detect_youtube(self):
        """Test detecting YouTube platform"""
        assert detect_platform("https://youtube.com/@username") == "youtube"
        assert detect_platform("https://www.youtube.com/@username") == "youtube"

    def test_detect_none_for_invalid_url(self):
        """Test that invalid URLs return None"""
        assert detect_platform("https://example.com") is None
        assert detect_platform("not a url") is None
        assert detect_platform("") is None

    def test_detect_platform_type_error_none(self):
        """Test TypeError for None input"""
        with pytest.raises(TypeError, match="url must be str, not NoneType"):
            detect_platform(None)

    def test_detect_platform_type_error_int(self):
        """Test TypeError for integer input"""
        with pytest.raises(TypeError, match="url must be str, not int"):
            detect_platform(123)

    def test_detect_platform_type_error_list(self):
        """Test TypeError for list input"""
        with pytest.raises(TypeError, match="url must be str, not list"):
            detect_platform(["https://linkedin.com/in/johndoe"])

    def test_detect_platform_type_error_dict(self):
        """Test TypeError for dict input"""
        with pytest.raises(TypeError, match="url must be str, not dict"):
            detect_platform({"url": "https://linkedin.com/in/johndoe"})

    def test_detect_platform_whitespace_handling(self):
        """Test that leading/trailing whitespace is properly stripped"""
        url = "  https://www.linkedin.com/in/johndoe/  "
        assert detect_platform(url) == "linkedin"
        assert detect_platform("   ") is None
        assert detect_platform("\t\n") is None

    def test_detect_platform_empty_string(self):
        """Test detect_platform with empty string"""
        assert detect_platform("") is None

    def test_detect_platform_case_insensitive(self):
        """Test case insensitive URL matching"""
        assert detect_platform("HTTPS://WWW.LINKEDIN.COM/IN/JOHNDOE/") == "linkedin"
        assert detect_platform("https://GITHUB.COM/USERNAME") == "github"


class TestModuleLevelIsValid:
    """Test is_valid() module-level function"""

    def test_is_valid_linkedin_personal(self):
        """Test validating LinkedIn personal URLs"""
        assert is_valid("linkedin", "https://www.linkedin.com/in/johndoe/") is True
        assert is_valid("linkedin", "http://linkedin.com/in/jane-smith") is True
        assert is_valid("linkedin", "https://example.com") is False

    def test_is_valid_linkedin_company(self):
        """Test validating LinkedIn company URLs"""
        assert is_valid("linkedin", "https://www.linkedin.com/company/acme/") is True
        assert is_valid("linkedin", "http://linkedin.com/company/techcorp") is True

    def test_is_valid_facebook(self):
        """Test validating Facebook URLs"""
        assert is_valid("facebook", "https://www.facebook.com/johndoe/") is True
        assert is_valid("facebook", "http://facebook.com/janedoe") is True
        assert is_valid("facebook", "https://example.com") is False

    def test_is_valid_github(self):
        """Test validating GitHub URLs"""
        assert is_valid("github", "https://github.com/username") is True
        assert is_valid("github", "https://example.com") is False

    def test_is_valid_x(self):
        """Test validating X (Twitter) URLs"""
        assert is_valid("x", "https://x.com/username") is True
        assert is_valid("x", "https://twitter.com/username") is True
        assert is_valid("x", "https://example.com") is False

    def test_is_valid_unknown_platform(self):
        """Test validating with unknown platform"""
        assert is_valid("unknown", "https://www.linkedin.com/in/johndoe/") is False
        assert is_valid("nonexistent", "https://github.com/username") is False

    def test_is_valid_type_error_none_url(self):
        """Test TypeError for None URL"""
        with pytest.raises(TypeError, match="url must be str, not NoneType"):
            is_valid("linkedin", None)

    def test_is_valid_type_error_none_platform(self):
        """Test TypeError for None platform name"""
        with pytest.raises(TypeError, match="platform_name must be str, not NoneType"):
            is_valid(None, "https://linkedin.com/in/johndoe")

    def test_is_valid_type_error_int_url(self):
        """Test TypeError for integer URL"""
        with pytest.raises(TypeError, match="url must be str, not int"):
            is_valid("linkedin", 123)

    def test_is_valid_type_error_int_platform(self):
        """Test TypeError for integer platform name"""
        with pytest.raises(TypeError, match="platform_name must be str, not int"):
            is_valid(123, "https://linkedin.com/in/johndoe")

    def test_is_valid_empty_string(self):
        """Test is_valid with empty string URL"""
        assert is_valid("linkedin", "") is False

    def test_is_valid_whitespace_only(self):
        """Test is_valid with whitespace only URL"""
        assert is_valid("linkedin", "   ") is False
        assert is_valid("linkedin", "\t\n") is False

    def test_is_valid_whitespace_handling(self):
        """Test that leading/trailing whitespace is properly stripped"""
        url = "  https://www.linkedin.com/in/johndoe/  "
        assert is_valid("linkedin", url) is True

    def test_is_valid_case_insensitive(self):
        """Test case insensitive URL matching"""
        assert is_valid("linkedin", "HTTPS://WWW.LINKEDIN.COM/IN/JOHNDOE/") is True
        assert is_valid("github", "https://GITHUB.COM/USERNAME") is True


class TestModuleLevelSanitize:
    """Test sanitize() module-level function"""

    def test_sanitize_linkedin_personal(self):
        """Test sanitizing LinkedIn personal URLs"""
        result = sanitize("linkedin", "https://www.linkedin.com/in/johndoe/")
        assert result == "https://linkedin.com/in/johndoe"
        
        result = sanitize("linkedin", "http://linkedin.com/in/jane-smith")
        assert result == "https://linkedin.com/in/jane-smith"

    def test_sanitize_linkedin_company(self):
        """Test sanitizing LinkedIn company URLs"""
        result = sanitize("linkedin", "https://www.linkedin.com/company/acme/")
        assert result == "https://linkedin.com/company/acme"
        
        result = sanitize("linkedin", "http://linkedin.com/company/techcorp")
        assert result == "https://linkedin.com/company/techcorp"

    def test_sanitize_facebook(self):
        """Test sanitizing Facebook URLs"""
        result = sanitize("facebook", "https://www.facebook.com/johndoe/")
        assert result == "https://facebook.com/johndoe"
        
        result = sanitize("facebook", "http://facebook.com/janedoe")
        assert result == "https://facebook.com/janedoe"

    def test_sanitize_github(self):
        """Test sanitizing GitHub URLs"""
        result = sanitize("github", "http://www.github.com/username")
        assert result == "https://github.com/username"
        
        result = sanitize("github", "https://github.com/username")
        assert result == "https://github.com/username"

    def test_sanitize_x(self):
        """Test sanitizing X (Twitter) URLs"""
        result = sanitize("x", "https://twitter.com/username")
        assert result == "https://x.com/username"
        
        result = sanitize("x", "https://mobile.twitter.com/username")
        assert result == "https://x.com/username"

    def test_sanitize_platform_not_found(self):
        """Test PlatformNotFoundError for unknown platform"""
        with pytest.raises(PlatformNotFoundError, match="Unknown platform"):
            sanitize("unknown", "https://linkedin.com/in/johndoe")
        
        with pytest.raises(PlatformNotFoundError, match="Unknown platform"):
            sanitize("nonexistent", "https://github.com/username")

    def test_sanitize_url_mismatch(self):
        """Test URLMismatchError for invalid URL"""
        with pytest.raises(URLMismatchError, match="does not match platform"):
            sanitize("linkedin", "https://example.com")
        
        with pytest.raises(URLMismatchError, match="does not match platform"):
            sanitize("github", "https://example.com")

    def test_sanitize_type_error_none_url(self):
        """Test TypeError for None URL"""
        with pytest.raises(TypeError, match="url must be str, not NoneType"):
            sanitize("linkedin", None)

    def test_sanitize_type_error_none_platform(self):
        """Test TypeError for None platform name"""
        with pytest.raises(TypeError, match="platform_name must be str, not NoneType"):
            sanitize(None, "https://linkedin.com/in/johndoe")

    def test_sanitize_type_error_int_url(self):
        """Test TypeError for integer URL"""
        with pytest.raises(TypeError, match="url must be str, not int"):
            sanitize("linkedin", 123)

    def test_sanitize_type_error_float_url(self):
        """Test TypeError for float URL"""
        with pytest.raises(TypeError, match="url must be str, not float"):
            sanitize("linkedin", 3.14)

    def test_sanitize_empty_string(self):
        """Test sanitize with empty string URL"""
        with pytest.raises(URLMismatchError, match="URL cannot be empty"):
            sanitize("linkedin", "")

    def test_sanitize_whitespace_only(self):
        """Test sanitize with whitespace only URL"""
        with pytest.raises(URLMismatchError, match="URL cannot be empty"):
            sanitize("linkedin", "   ")
        with pytest.raises(URLMismatchError, match="URL cannot be empty"):
            sanitize("linkedin", "\t\n")

    def test_sanitize_whitespace_handling(self):
        """Test that leading/trailing whitespace is properly stripped"""
        url = "  https://www.linkedin.com/in/johndoe/  "
        result = sanitize("linkedin", url)
        assert result == "https://linkedin.com/in/johndoe"

    def test_sanitize_unicode_characters(self):
        """Test sanitizing URLs with Unicode characters"""
        unicode_url = "https://www.linkedin.com/in/josé-garcía/"
        result = sanitize("linkedin", unicode_url)
        assert result == "https://linkedin.com/in/josé-garcía"


class TestModuleLevelListPlatforms:
    """Test list_platforms() module-level function"""

    def test_list_platforms_returns_list(self):
        """Test that list_platforms returns a list"""
        platforms = list_platforms()
        assert isinstance(platforms, list)

    def test_list_platforms_non_empty(self):
        """Test that list_platforms returns non-empty list by default"""
        platforms = list_platforms()
        assert len(platforms) > 0
        assert len(platforms) >= 50  # Should have 50+ predefined platforms

    def test_list_platforms_matches_class_method(self):
        """Test that module function matches class method"""
        module_result = set(list_platforms())
        class_result = set(SocialLinks().list_platforms())
        assert module_result == class_result
