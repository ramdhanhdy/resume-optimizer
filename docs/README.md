# Resume Optimizer Documentation

Welcome to the Resume Optimizer documentation! This directory contains comprehensive documentation organized by category for developers, users, and system administrators.

## 📚 Documentation Structure

### 🚀 [Setup Guides](./setup/)

Getting started and configuration documentation:

- **[SETUP.md](./setup/SETUP.md)** - Main setup guide for the Resume Optimizer
  - Installation instructions for backend and frontend
  - Prerequisites and dependencies
  - Environment configuration
  - Development server startup
  - Common setup issues and solutions

- **[GEMINI_SETUP.md](./setup/GEMINI_SETUP.md)** - Google Gemini API integration guide
  - Getting your Gemini API key
  - Available models and pricing
  - Configuration steps
  - Testing your setup
  - Troubleshooting

### 🏗️ [Architecture](./architecture/)

System design and agent architecture:

- **[AGENTS_DESIGN_PATTERN.md](./architecture/AGENTS_DESIGN_PATTERN.md)** - Agent design and pattern mapping
  - Multi-agent pipeline overview
  - Agent responsibilities and orchestration
  - Google Cloud design pattern mapping
  - Key implementation files

### 🔌 [Integrations](./integrations/)

Third-party service integration documentation:

- **[INTEGRATION_SUMMARY.md](./integrations/INTEGRATION_SUMMARY.md)** - Overall integration architecture
  - Full-stack integration overview
  - Backend and frontend migration details
  - API endpoint documentation
  - Technical architecture

- **[GEMINI_INTEGRATION_SUMMARY.md](./integrations/GEMINI_INTEGRATION_SUMMARY.md)** - Gemini API technical details
  - Implementation details and code architecture
  - Model configuration and capabilities
  - Cost tracking and optimization
  - Testing and verification procedures

### 📋 [Technical Specifications](./specs/)

Detailed technical specifications for core features:

- **[Streaming Specification](./specs/streaming_specification.md)** - Real-time streaming architecture
  - Server-Sent Events implementation
  - Event types and data structures
  - Performance requirements
  - Security considerations

- **[UI Component Specification](./specs/ui_component_specification.md)** - Frontend component design
  - React component architecture
  - Styling and animation specifications
  - Responsive design requirements
  - Accessibility guidelines

- **[Gemini Integration Specification](./specs/gemini_integration_specification.md)** - LLM provider integration
  - API client implementation details
  - Model capabilities and limitations
  - Cost tracking and optimization strategies

- **[Parallel Insight Extractor](./specs/parallel_insight_extractor.md)** - Parallel processing architecture
  - Insight extraction algorithms
  - Performance optimization strategies

- **[Deployment Specifications](./specs/deployment/)** - Production deployment guides
  - **[Quick Deployment Guide](./specs/deployment/quick_deployment_guide.md)** - 30-minute production setup
  - **[Vercel + Railway](./specs/deployment/vercel_deployment_specification.md)** - Hybrid deployment approach
  - **[Railway-Only](./specs/deployment/railway_only_deployment_specification.md)** - Single-platform solution
  - **[Platform Alternatives](./specs/deployment/deployment_alternatives_specification.md)** - Multiple deployment options
  - **[Technical Notes](./specs/deployment/deployment_technical_notes.md)** - Architecture decisions and analysis

### 🔧 [Troubleshooting](./troubleshooting/)

Comprehensive troubleshooting guides for common issues:

- **[Component Flashing/Disappearing](./troubleshooting/COMPONENT_FLASHING_FIX.md)** - UI component rendering issues
  - Problem diagnosis and root cause analysis
  - Step-by-step resolution procedures
  - Prevention measures and best practices

- **[Job URL Processing](./troubleshooting/JOB_URL_BUG_FIX.md)** - Job posting URL handling issues
  - Data flow problems and solutions
  - Frontend-backend integration fixes
  - Verification procedures

- **[Tailwind CSS v4 Configuration](./troubleshooting/TAILWIND_V4_FIX.md)** - CSS framework configuration issues
  - Theme system migration guide
  - Styling and appearance problems
  - Build configuration fixes

- **[Resume Display Issues](./troubleshooting/RESUME_DISPLAY_TROUBLESHOOTING.md)** - Content display problems
  - Empty resume content on reveal screen
  - Database content verification
  - API endpoint troubleshooting

### 📖 [Documentation Index](./DOCUMENTATION_INDEX.md)

- **[DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md)** - Complete documentation navigation
  - Comprehensive file organization and purpose
  - Quick access links by category
  - Documentation standards and guidelines

## 🎯 Quick Navigation

### 👋 For New Users
1. **Start Here**: [SETUP.md](./setup/SETUP.md) - Installation and first run
2. **Configure**: [GEMINI_SETUP.md](./setup/GEMINI_SETUP.md) - Optional API setup
3. **Understand**: [INTEGRATION_SUMMARY.md](./integrations/INTEGRATION_SUMMARY.md) - System overview

### 🛠️ For Developers
1. **Architecture**: [Agent Design Pattern](./architecture/AGENTS_DESIGN_PATTERN.md) - Backend design
2. **Frontend**: [UI Component Specification](./specs/ui_component_specification.md) - Component development
3. **Streaming**: [Streaming Specification](./specs/streaming_specification.md) - Real-time features
4. **Integration**: [Gemini Integration](./specs/gemini_integration_specification.md) - LLM providers
5. **Deployment**: [Deployment Specifications](./specs/deployment/) - Production setup guides

### 🔍 For Troubleshooting
1. **UI Issues**: [Component Flashing](./troubleshooting/COMPONENT_FLASHING_FIX.md)
2. **Functionality**: [Job URL Processing](./troubleshooting/JOB_URL_BUG_FIX.md)
3. **Styling**: [Tailwind CSS v4](./troubleshooting/TAILWIND_V4_FIX.md)
4. **Display**: [Resume Display](./troubleshooting/RESUME_DISPLAY_TROUBLESHOOTING.md)

### 📊 For System Administrators
1. **Deployment**: [Deployment Specifications](./specs/deployment/) - Production deployment options
2. **Integration**: [Integration Summary](./integrations/INTEGRATION_SUMMARY.md) - System architecture
3. **Setup**: [Setup Guide](./setup/SETUP.md) - Deployment configuration
4. **Specifications**: All [Technical Specifications](./specs/) for detailed requirements

## 🚀 Quick Start

1. **Clone and Setup**: Follow [SETUP.md](./setup/SETUP.md)
2. **Configure APIs**: Add your API keys to environment files
3. **Start Development**: Run backend and frontend servers
4. **Review Architecture**: Read [Integration Summary](./integrations/INTEGRATION_SUMMARY.md)

## 📋 Documentation Standards

### File Organization
- **Setup guides**: `/setup/` directory
- **Specifications**: `/specs/` directory with `_specification.md` suffix
- **Troubleshooting**: `/troubleshooting/` directory with `_TROUBLESHOOTING.md` suffix
- **Architecture**: `/architecture/` directory
- **Integrations**: `/integrations/` directory

### Document Structure
Each document includes:
- Clear purpose and scope
- Problem/requirement description
- Step-by-step procedures
- Verification and testing
- Related issues and prevention

### Version Information
- Last updated dates included
- Severity/impact where relevant
- Version tracking for major changes

## 🔗 Additional Resources

### External Documentation
- **Main Project README**: [../README.md](../README.md)
- **Backend README**: [../backend/README.md](../backend/README.md)
- **Frontend Source**: `../frontend/src/`

### Related Projects
- **JobHunt Agent**: Original backend prototype
- **CVit**: Original frontend prototype

## 🤝 Contributing to Documentation

### Adding New Documentation
1. Choose appropriate directory based on document type
2. Follow naming conventions (see standards above)
3. Include required sections and structure
4. Update [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md)
5. Update this README.md with new links

### Updating Existing Documents
1. Update version information and dates
2. Maintain consistent formatting and structure
3. Verify all links and references
4. Test any procedures or code examples

### Quality Standards
- Use clear, concise language
- Include code examples where helpful
- Provide step-by-step instructions
- Add troubleshooting sections
- Cross-reference related documents

---

**Last Updated**: January 31, 2025  
**Maintainer**: Development Team  
**Documentation Version**: 2.0

For the complete navigation experience, see the [Documentation Index](./DOCUMENTATION_INDEX.md).
