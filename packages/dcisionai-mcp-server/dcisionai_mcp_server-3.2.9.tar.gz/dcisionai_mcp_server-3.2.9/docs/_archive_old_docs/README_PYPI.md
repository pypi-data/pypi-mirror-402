# DcisionAI MCP Server

**AI-Powered Optimization for Cursor, Claude Desktop & VS Code**

[![PyPI version](https://badge.fury.io/py/dcisionai-mcp-server.svg)](https://badge.fury.io/py/dcisionai-mcp-server)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Solve complex optimization problems directly in your IDE using natural language. Get mathematically-verified solutions with **90%+ trust scores** in seconds.

---

## 🚀 **Quick Start**

### Installation (Zero Configuration!)

```bash
# That's it! No installation needed with uvx
```

### Configure Your IDE

**For Cursor or Claude Desktop:**

Add to your MCP config file (`~/Library/Application\ Support/Claude/claude_desktop_config.json` on Mac):

```json
{
  "mcpServers": {
    "dcisionai": {
      "command": "uvx",
      "args": ["dcisionai-mcp-server@latest"],
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}"
      },
      "autoApprove": ["dcisionai_solve"]
    }
  }
}
```

**For VS Code:**
Add to your `.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "dcisionai": {
      "command": "uvx",
      "args": ["dcisionai-mcp-server@latest"],
      "env": {
        "OPENAI_API_KEY": "your-openai-key",
        "ANTHROPIC_API_KEY": "your-anthropic-key"
      }
    }
  }
}
```

### Use It!

In Cursor or Claude Desktop, just ask:

```
"Use DcisionAI to optimize my $500K portfolio concentrated in tech stocks"

"Use DcisionAI to optimize delivery routes for 20 customers"

"Use DcisionAI to optimize employee scheduling for 30 workers across 50 shifts"
```

---

## ✨ **What Can It Do?**

### 📊 **Finance**
- Portfolio rebalancing with risk constraints
- Trading schedule optimization  
- Asset allocation with concentration limits
- Private equity exit timing

### 🏪 **Retail**
- Store layout optimization (shelf space allocation)
- Promotion scheduling with budget constraints
- Inventory placement optimization

### 🚚 **Logistics**
- Vehicle routing (VRP) with time windows
- Delivery route optimization
- Fleet allocation

### 👥 **Workforce**
- Employee scheduling with skill requirements
- Shift rostering with labor rules
- Resource allocation

### 🏭 **Manufacturing**
- Job shop scheduling
- Maintenance scheduling
- Production planning

---

## 🎯 **Why DcisionAI?**

### **1. Natural Language → Optimized Solution**
```
You: "Optimize 20 products across 5 shelves to maximize revenue"
   ⬇️
DcisionAI: Automatically classifies, extracts data, builds model, solves
   ⬇️
Result: Complete solution with 90%+ trust score in 15 seconds
```

### **2. Mathematical Proof**
Every solution includes:
- ✅ Constraint Verification
- ✅ Monte Carlo Simulation (1000 trials)
- ✅ Optimality Certificate
- ✅ Sensitivity Analysis
- ✅ Benchmark Comparison
- ✅ Cross-Validation (HiGHS vs DAME)

### **3. Business-Friendly**
- LLM-generated implementation steps
- Risk analysis & assumptions
- "What-if" scenarios
- Plain English explanations

### **4. Dual-Solver Validation**
- **DAME** (DcisionAI Micro-differential Evolutionary Algorithm) - Works for ANY problem
- **HiGHS** - Provably optimal for LP/MIP
- Parallel execution → Higher trust scores

---

## 📈 **Example Output**

```python
{
  "status": "success",
  "industry": "RETAIL",
  "domain": "Store Layout Optimization",
  
  # Solution
  "objective_value": 0.427,
  "solution": {...},
  
  # Trust & Validation
  "trust_score": 0.92,  # 92% confidence!
  "certification": "VERIFIED",
  "mathematical_proof": {
    "constraint_verification": {"status": "verified", "confidence": 1.0},
    "monte_carlo_simulation": {"status": "verified", "confidence": 0.999},
    "optimality_certificate": {"status": "verified", "gap": 0.047},
    "sensitivity_analysis": {"status": "verified", "confidence": 1.0},
    "benchmark_comparison": {"status": "verified", "improvement": 42.3},
    "cross_validation": {"status": "verified", "agreement": 0.98}
  },
  
  # Business Insights
  "business_interpretation": {
    "summary": "Systematically optimized product placement across 5 shelves...",
    "key_decisions": {...},
    "implementation_steps": [...],
    "risks_and_assumptions": [...],
    "what_if_scenarios": [...]
  }
}
```

---

## 🔧 **Advanced Usage**

### Validation Modes

```json
{
  "validation_mode": "auto"      // Smart routing (default)
  "validation_mode": "parallel"  // Both HiGHS + DAME (max trust)
  "validation_mode": "fast"      // Fastest solver only
  "validation_mode": "exact"     // HiGHS only (LP/MIP optimal)
  "validation_mode": "heuristic" // DAME only (any problem)
}
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | **Yes** | OpenAI API key for LLM |
| `ANTHROPIC_API_KEY` | **Yes** | Anthropic API key for Claude |
| `POLYGON_API_KEY` | No | For real-time market data (finance domains) |
| `ALPHA_VANTAGE_API_KEY` | No | For economic/commodity data (finance domains) |

**Note**: DcisionAI uses internal infrastructure (Supabase) for domain configurations. No additional setup needed!

---

## 📚 **Technical Details**

### **DAME Algorithm**
- **D**cisionAI **M**icro-differential **E**volutionary **A**lgorithm
- Proprietary heuristic solver
- Handles ANY optimization problem
- 0.1-3% optimality gap in 0.5-5 seconds

### **HiGHS Integration**
- Open-source LP/MIP solver
- Provably optimal solutions
- Parallel validation with DAME
- Used for cross-validation proofs

### **Trust Scoring**
Weighted average of 6 proofs:
- Constraint Verification: 25%
- Monte Carlo Simulation: 20%
- Optimality Certificate: 15%
- Sensitivity Analysis: 15%
- Benchmark Comparison: 10%
- Cross-Validation: 15%

---

## 🤝 **Contributing**

We welcome contributions! See our [GitHub repository](https://github.com/ameydhavle/dcisionai-mcp-platform) for:
- Bug reports
- Feature requests
- Pull requests
- Documentation improvements

---

## 📄 **License**

MIT License - See [LICENSE](https://github.com/ameydhavle/dcisionai-mcp-platform/blob/main/LICENSE) for details.

---

## 🔗 **Links**

- **Homepage**: [dcisionai.com](https://dcisionai.com)
- **GitHub**: [github.com/ameydhavle/dcisionai-mcp-platform](https://github.com/ameydhavle/dcisionai-mcp-platform)
- **Issues**: [GitHub Issues](https://github.com/ameydhavle/dcisionai-mcp-platform/issues)
- **Research Paper**: [DcisionAI Technical Paper](https://github.com/ameydhavle/dcisionai-mcp-platform/blob/main/papers/DcisionAI.pdf)

---

## 💡 **Support**

- 📧 Email: amey@dcisionai.com
- 🐛 Issues: [GitHub Issues](https://github.com/ameydhavle/dcisionai-mcp-platform/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/ameydhavle/dcisionai-mcp-platform/discussions)

---

**Made with ❤️ by the DcisionAI Team**

