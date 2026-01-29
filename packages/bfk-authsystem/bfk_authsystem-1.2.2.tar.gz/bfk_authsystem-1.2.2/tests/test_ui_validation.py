"""
Testes para validacao de campos nos dialogos UI.

Estes testes focam na logica de validacao sem necessidade
de renderizar a interface grafica.
"""
import pytest
import re

# Tentar importar PyQt5
try:
    from PyQt5.QtWidgets import QApplication
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

# Skip se PyQt5 nao disponivel
pytestmark = pytest.mark.skipif(
    not PYQT_AVAILABLE,
    reason="PyQt5 nao disponivel"
)


class TestLicenseKeyValidation:
    """Testes para validacao de chave de licenca."""

    # Padrao da chave: BFK-XXXX-XXXX-XXXX
    LICENSE_KEY_PATTERN = r'^BFK-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$'

    def test_valid_license_key(self):
        """Chave de licenca valida."""
        valid_keys = [
            'BFK-ABCD-1234-WXYZ',
            'BFK-0000-0000-0000',
            'BFK-AAAA-BBBB-CCCC',
            'BFK-1234-5678-9ABC'
        ]
        for key in valid_keys:
            assert re.match(self.LICENSE_KEY_PATTERN, key), f"Chave deveria ser valida: {key}"

    def test_invalid_license_key_format(self):
        """Chaves com formato invalido."""
        invalid_keys = [
            'ABC-1234-5678-9ABC',  # Prefixo errado
            'BFK-123-5678-9ABC',   # Grupo curto
            'BFK-12345-5678-9ABC', # Grupo longo
            'BFK-1234-5678',       # Faltando grupo
            'bfk-1234-5678-9abc',  # Minusculas
            'BFK1234-5678-9ABC',   # Sem hifen
            '',                     # Vazio
            'BFK-XXXX-XXXX-XXX!',  # Caractere especial
        ]
        for key in invalid_keys:
            assert not re.match(self.LICENSE_KEY_PATTERN, key), f"Chave deveria ser invalida: {key}"

    def test_license_key_format_function(self):
        """Funcao de formatacao de chave."""
        def format_key(text: str) -> str:
            """Formata texto para padrao de chave."""
            clean = re.sub(r'[^A-Za-z0-9]', '', text.upper())

            if clean and not clean.startswith('BFK'):
                if len(clean) <= 3:
                    if 'BFK'.startswith(clean):
                        pass
                    else:
                        clean = 'BFK' + clean
                else:
                    clean = 'BFK' + clean

            formatted = ''
            if len(clean) <= 3:
                formatted = clean
            else:
                formatted = clean[:3] + '-'
                remaining = clean[3:]
                for i, char in enumerate(remaining):
                    if i > 0 and i % 4 == 0 and i < 12:
                        formatted += '-'
                    formatted += char

            if len(formatted) > 19:
                formatted = formatted[:19]

            return formatted

        # Testes de formatacao
        assert format_key('BFK12345678ABCD') == 'BFK-1234-5678-ABCD'
        assert format_key('bfk12345678abcd') == 'BFK-1234-5678-ABCD'
        assert format_key('12345678ABCD') == 'BFK-1234-5678-ABCD'
        assert format_key('BFK') == 'BFK'
        assert format_key('') == ''


class TestMFACodeValidation:
    """Testes para validacao de codigo MFA."""

    # Padrao do codigo MFA: 6 digitos
    MFA_CODE_PATTERN = r'^\d{6}$'

    def test_valid_mfa_code(self):
        """Codigos MFA validos."""
        valid_codes = [
            '000000',
            '123456',
            '999999',
            '012345'
        ]
        for code in valid_codes:
            assert re.match(self.MFA_CODE_PATTERN, code), f"Codigo deveria ser valido: {code}"

    def test_invalid_mfa_code(self):
        """Codigos MFA invalidos."""
        invalid_codes = [
            '12345',     # 5 digitos
            '1234567',   # 7 digitos
            'ABCDEF',    # Letras
            '12345A',    # Letra no final
            '',          # Vazio
            '123 456',   # Espaco
        ]
        for code in invalid_codes:
            assert not re.match(self.MFA_CODE_PATTERN, code), f"Codigo deveria ser invalido: {code}"


class TestRecoveryCodeValidation:
    """Testes para validacao de codigo de recuperacao."""

    # Padrao do recovery code: XXXX-XXXX
    RECOVERY_CODE_PATTERN = r'^[A-Z0-9]{4}-[A-Z0-9]{4}$'

    def test_valid_recovery_code(self):
        """Codigos de recuperacao validos."""
        valid_codes = [
            'ABCD-1234',
            '1234-ABCD',
            'AAAA-0000',
            'X1Y2-Z3W4'
        ]
        for code in valid_codes:
            assert re.match(self.RECOVERY_CODE_PATTERN, code), f"Codigo deveria ser valido: {code}"

    def test_invalid_recovery_code(self):
        """Codigos de recuperacao invalidos."""
        invalid_codes = [
            'ABC-1234',    # Grupo curto
            'ABCDE-1234',  # Grupo longo
            'abcd-1234',   # Minusculas
            'ABCD1234',    # Sem hifen
            '',            # Vazio
        ]
        for code in invalid_codes:
            assert not re.match(self.RECOVERY_CODE_PATTERN, code), f"Codigo deveria ser invalido: {code}"


class TestPasswordValidation:
    """Testes para validacao de senha."""

    def validate_password(self, password: str) -> tuple:
        """
        Valida senha conforme regras.

        Returns:
            (is_valid, errors)
        """
        errors = []

        if len(password) < 8:
            errors.append('Senha deve ter pelo menos 8 caracteres')

        if not re.search(r'[A-Z]', password):
            errors.append('Senha deve conter letra maiuscula')

        if not re.search(r'[a-z]', password):
            errors.append('Senha deve conter letra minuscula')

        if not re.search(r'\d', password):
            errors.append('Senha deve conter numero')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('Senha deve conter caractere especial')

        return (len(errors) == 0, errors)

    def test_valid_password(self):
        """Senhas validas."""
        valid_passwords = [
            'Test123!@#',
            'SecureP@ss1',
            'MyPassword1!',
            'Abcdefg1!'
        ]
        for pwd in valid_passwords:
            is_valid, errors = self.validate_password(pwd)
            assert is_valid, f"Senha deveria ser valida: {pwd} - Erros: {errors}"

    def test_password_too_short(self):
        """Senha muito curta."""
        is_valid, errors = self.validate_password('Test1!')
        assert not is_valid
        assert 'pelo menos 8 caracteres' in errors[0]

    def test_password_no_uppercase(self):
        """Senha sem maiuscula."""
        is_valid, errors = self.validate_password('test123!@#')
        assert not is_valid
        assert any('maiuscula' in e for e in errors)

    def test_password_no_lowercase(self):
        """Senha sem minuscula."""
        is_valid, errors = self.validate_password('TEST123!@#')
        assert not is_valid
        assert any('minuscula' in e for e in errors)

    def test_password_no_number(self):
        """Senha sem numero."""
        is_valid, errors = self.validate_password('TestPass!@#')
        assert not is_valid
        assert any('numero' in e for e in errors)

    def test_password_no_special(self):
        """Senha sem caractere especial."""
        is_valid, errors = self.validate_password('TestPass123')
        assert not is_valid
        assert any('especial' in e for e in errors)


class TestEmailValidation:
    """Testes para validacao de email."""

    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    def test_valid_email(self):
        """Emails validos."""
        valid_emails = [
            'user@example.com',
            'user.name@example.com',
            'user+tag@example.org',
            'user123@sub.domain.com'
        ]
        for email in valid_emails:
            assert re.match(self.EMAIL_PATTERN, email), f"Email deveria ser valido: {email}"

    def test_invalid_email(self):
        """Emails invalidos."""
        invalid_emails = [
            'user@',
            '@example.com',
            'user@.com',
            'user@example',
            '',
            'user example.com',
            'user@@example.com'
        ]
        for email in invalid_emails:
            assert not re.match(self.EMAIL_PATTERN, email), f"Email deveria ser invalido: {email}"


class TestUsernameValidation:
    """Testes para validacao de username."""

    # Padrao: 3-50 caracteres, alfanumerico e underscore
    USERNAME_PATTERN = r'^[a-zA-Z0-9_]{3,50}$'

    def test_valid_username(self):
        """Usernames validos."""
        valid_usernames = [
            'user',
            'user123',
            'user_name',
            'User_Name_123',
            'abc'
        ]
        for username in valid_usernames:
            assert re.match(self.USERNAME_PATTERN, username), f"Username deveria ser valido: {username}"

    def test_invalid_username(self):
        """Usernames invalidos."""
        invalid_usernames = [
            'ab',            # Muito curto
            'user name',     # Espaco
            'user@name',     # Caractere especial
            'user.name',     # Ponto
            '',              # Vazio
            'a' * 51         # Muito longo
        ]
        for username in invalid_usernames:
            assert not re.match(self.USERNAME_PATTERN, username), f"Username deveria ser invalido: {username}"
