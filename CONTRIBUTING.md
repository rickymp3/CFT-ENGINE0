# Contributing to CFT-ENGINE0

We love your input! We want to make contributing to CFT-ENGINE0 as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

### Pull Requests

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code follows the existing style.
6. Issue that pull request!

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/CFT-ENGINE0.git
cd CFT-ENGINE0

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest

# Run stress tests
python -m pytest tests/test_stress.py -v
```

## Code Style

- Follow PEP8 for Python code
- Use type hints where possible
- Write docstrings for all public functions/classes
- Keep functions focused and under 50 lines when possible
- Use meaningful variable names

### Example:
```python
def calculate_lighting(position: Vec3, normal: Vec3, light_color: Vec3) -> Vec3:
    """
    Calculate lighting at a point using Blinn-Phong model.
    
    Args:
        position: World-space position
        normal: Surface normal (normalized)
        light_color: RGB color of light source
        
    Returns:
        Final lit color as Vec3
    """
    # Implementation here
    pass
```

## Testing Requirements

All contributions must include tests:

### Unit Tests
Place in `tests/test_*.py`:
```python
def test_new_feature():
    """Test the new feature works correctly"""
    result = new_feature(input_data)
    assert result == expected_output
```

### Stress Tests
For performance-critical code, add to `tests/test_stress.py`:
```python
def test_new_feature_performance():
    """Ensure new feature meets performance targets"""
    profiler = create_profiler(base)
    
    # Run feature
    with profiler.zone("new_feature"):
        for _ in range(1000):
            new_feature()
    
    # Assert performance
    assert profiler.get_zone_stats("new_feature").avg_ms < 10.0
```

## Documentation

- Update `README.md` for user-facing changes
- Add system documentation to `AAA_SYSTEMS_COMPLETE_GUIDE.md`
- Create examples in `examples/` for new features
- Include docstrings with type hints

## Performance Standards

All code must meet these performance targets:

- **Frame time:** <33ms (30 FPS minimum)
- **Memory growth:** <5MB/hour in long-running tests
- **Load times:** <5s for typical assets
- **No memory leaks:** Must pass `test_stress.py::TestMemory`

## Bug Reports

Great bug reports include:

- **Summary**: Quick overview of the issue
- **Steps to reproduce**: Be specific!
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **System info**: OS, Python version, Panda3D version
- **Logs/Screenshots**: If applicable

### Example:
```markdown
## Bug: Physics bodies fall through floor at high speeds

**Steps to Reproduce:**
1. Create a rigid body sphere
2. Set velocity to (0, 0, -100)
3. Place floor at z=0
4. Run simulation

**Expected:** Sphere bounces off floor
**Actual:** Sphere passes through floor

**System:** Ubuntu 20.04, Python 3.12, Panda3D 1.10.15
```

## Feature Requests

We use GitHub Issues to track feature requests. Before creating:

1. Check if it already exists
2. Explain the problem it solves
3. Provide use cases
4. Suggest implementation if possible

### Example:
```markdown
## Feature Request: Volumetric Fog System

**Problem:** Current fog is uniform, unrealistic for outdoor scenes

**Proposed Solution:** 
- Height-based fog density
- Animated noise texture for variation
- Integration with weather system

**Use Cases:**
- Spooky forest environments
- Realistic mountain valleys
- Dynamic weather transitions

**Implementation Notes:**
- Could use existing volumetric system as base
- Add height falloff parameter
- Expose fog color to weather system
```

## Code Review Process

The core team reviews Pull Requests weekly. We look for:

1. **Functionality**: Does it work as intended?
2. **Tests**: Are there tests? Do they pass?
3. **Performance**: Does it meet our standards?
4. **Documentation**: Is it documented?
5. **Style**: Does it follow conventions?

## Community Guidelines

### Be Respectful
- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what's best for the community

### Be Professional
- Keep discussions on-topic
- No spam or self-promotion
- No harassment or personal attacks
- Respect maintainer decisions

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

## Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md` file
- Release notes
- Project README

## Questions?

Feel free to:
- Open a GitHub Discussion
- Join our Discord (link in README)
- Email maintainers (see README)

## Thank You!

Your contributions make CFT-ENGINE0 better for everyone. We appreciate your time and effort! 🎉
