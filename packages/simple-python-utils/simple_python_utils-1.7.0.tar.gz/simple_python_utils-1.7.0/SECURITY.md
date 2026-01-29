# Security Policy

## 🔒 Supported Versions

We actively support security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | ✅ Yes             |
| < 1.0   | ❌ No              |

## 🚨 Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these guidelines:

### 🚑 For Critical/High Severity Issues

**DO NOT** create a public issue. Instead:

1. **Email directly**: [fjmpereira20@users.noreply.github.com](mailto:fjmpereira20@users.noreply.github.com)
2. **Subject line**: `[SECURITY] Simple Python Utils - [Brief Description]`
3. **Include**:
   - Detailed description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact and exploitation scenarios
   - Any suggested fixes or mitigations
   - Your contact information for follow-up

### 📊 For Low/Medium Severity Issues

You may create a private issue or email directly.

### 🕰️ Response Timeline

- **Acknowledgment**: Within 24 hours
- **Initial assessment**: Within 72 hours
- **Regular updates**: Every 5 business days
- **Resolution target**: Based on severity
  - Critical: 1-7 days
  - High: 7-14 days
  - Medium: 14-30 days
  - Low: 30-90 days

## 🛱️ Security Measures

### 🔍 Automated Security

- **Dependency scanning**: Automated via Dependabot
- **Code scanning**: Bandit static analysis
- **Vulnerability monitoring**: Safety checks
- **CI/CD security**: Secure secrets management

### 🛡️ Security Best Practices

- **No external dependencies** in production code
- **Type validation** for all inputs
- **Error handling** that doesn't leak information
- **Secure development environment** with pre-commit hooks
- **Regular dependency updates**

## 🎦 Disclosure Process

1. **Investigation**: We investigate and validate the report
2. **Fix development**: We develop and test a fix
3. **Coordination**: We coordinate release timing with reporter
4. **Release**: We release the security fix
5. **Disclosure**: We publicly disclose (with credit to reporter)

### 🏆 Credit and Recognition

Security researchers who responsibly disclose vulnerabilities will:

- Be credited in the security advisory
- Be mentioned in release notes (with permission)
- Receive our sincere gratitude 🙏

## 🔍 Security Contact

- **Primary**: [fjmpereira20@users.noreply.github.com](mailto:fjmpereira20@users.noreply.github.com)
- **GitHub**: [@fjmpereira20](https://github.com/fjmpereira20)

## 📊 Vulnerability Assessment

### 🎨 Severity Levels

- **Critical**: Remote code execution, privilege escalation
- **High**: Information disclosure, authentication bypass
- **Medium**: Denial of service, data corruption
- **Low**: Information leakage, minor security concerns

### 🎢 Out of Scope

- Issues in dependencies (report to respective maintainers)
- Social engineering attacks
- Physical security issues
- Issues requiring physical access to the system
- Theoretical vulnerabilities without proof of concept

## 📝 Security Updates

Security updates will be:

- **Clearly marked** in release notes
- **Backported** to supported versions when possible
- **Announced** via GitHub Security Advisories
- **Documented** in the changelog

## 🔗 Additional Resources

- [GitHub Security Advisories](https://github.com/fjmpereira20/simple-python-utils/security/advisories)
- [Python Security Documentation](https://docs.python.org/3/library/security_warnings.html)
- [OWASP Python Security](https://owasp.org/www-project-python-security/)

---

**Thank you for helping keep Simple Python Utils secure! 🔒**