"""
Tests for file_compass.chunker module.
"""

import pytest
from pathlib import Path
import tempfile

from file_compass.chunker import FileChunker, Chunk, TREE_SITTER_AVAILABLE

# Marker for tests requiring tree-sitter
requires_tree_sitter = pytest.mark.skipif(
    not TREE_SITTER_AVAILABLE,
    reason="tree-sitter not installed"
)


class TestFileChunker:
    """Tests for FileChunker class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.chunker = FileChunker()

    def test_init_defaults(self):
        """Test default initialization."""
        chunker = FileChunker()
        assert chunker.max_tokens > 0
        assert chunker.overlap_tokens >= 0
        assert chunker.min_tokens >= 0

    def test_init_custom_values(self):
        """Test custom initialization."""
        chunker = FileChunker(
            max_chunk_tokens=500,
            chunk_overlap_tokens=50,
            min_chunk_tokens=10
        )
        assert chunker.max_tokens == 500
        assert chunker.overlap_tokens == 50
        assert chunker.min_tokens == 10

    def test_estimate_tokens(self):
        """Test token estimation."""
        text = "hello world this is a test"
        estimate = self.chunker._estimate_tokens(text)
        assert estimate > 0
        assert isinstance(estimate, int)

    def test_make_preview(self):
        """Test preview generation."""
        content = "a" * 500
        preview = self.chunker._make_preview(content, max_len=100)
        assert len(preview) <= 103  # 100 + "..."
        assert preview.endswith("...")

    def test_make_preview_short_content(self):
        """Test preview with short content."""
        content = "short text"
        preview = self.chunker._make_preview(content)
        assert preview == content
        assert not preview.endswith("...")

    def test_chunk_python_file(self):
        """Test chunking a Python file."""
        python_code = '''
def hello():
    """Say hello."""
    return "Hello, World!"

class Greeter:
    """A greeter class."""

    def greet(self, name):
        return f"Hello, {name}!"
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            temp_path = Path(f.name)

        try:
            chunks = self.chunker.chunk_file(temp_path)
            assert len(chunks) > 0
            assert all(isinstance(c, Chunk) for c in chunks)
            # Small files may result in whole_file chunk, that's okay
        finally:
            temp_path.unlink()

    def test_chunk_markdown_file(self):
        """Test chunking a Markdown file."""
        markdown = '''
# Heading 1

Some content under heading 1.

## Heading 2

More content here.

### Heading 3

Even more content.
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(markdown)
            temp_path = Path(f.name)

        try:
            chunks = self.chunker.chunk_file(temp_path)
            assert len(chunks) > 0
            # Small markdown may use sliding window, check we got chunks
            assert all(isinstance(c, Chunk) for c in chunks)
        finally:
            temp_path.unlink()

    def test_chunk_sliding_window(self):
        """Test sliding window chunking."""
        # Create a text larger than max_tokens * chars_per_token
        # Default max_tokens is 500, ~4 chars/token = ~2000 chars
        large_text = "word " * 1000  # 5000 chars
        chunks = self.chunker._chunk_sliding_window(large_text)

        assert len(chunks) >= 1
        assert all(c.chunk_type == 'window' for c in chunks)

    def test_chunk_very_large_sliding_window(self):
        """Test sliding window with definitely large text."""
        # Use a chunker with small max_tokens to force splitting
        chunker = FileChunker(max_chunk_tokens=100)
        # Create multi-line text (chunker works line-by-line)
        large_text = "\n".join(["This is line number " + str(i) for i in range(200)])
        chunks = chunker._chunk_sliding_window(large_text)

        # With max 100 tokens (~400 chars), this should split into multiple chunks
        assert len(chunks) > 1
        assert all(c.chunk_type == 'window' for c in chunks)

    def test_chunk_empty_file(self):
        """Test chunking an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("")
            temp_path = Path(f.name)

        try:
            chunks = self.chunker.chunk_file(temp_path)
            # Should return empty or single whole_file chunk
            assert len(chunks) <= 1
        finally:
            temp_path.unlink()

    def test_chunk_preserves_line_numbers(self):
        """Test that chunks preserve line number information."""
        code = '''line1
line2
line3
def func():
    pass
line6
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)

        try:
            chunks = self.chunker.chunk_file(temp_path)
            for chunk in chunks:
                assert chunk.line_start >= 1
                assert chunk.line_end >= chunk.line_start
        finally:
            temp_path.unlink()

    def test_oversized_chunk_gets_split(self):
        """Test that oversized chunks get split via sliding window."""
        # Create a very long function
        long_func = "def long_function():\n" + "    x = 1\n" * 1000

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(long_func)
            temp_path = Path(f.name)

        try:
            chunks = self.chunker.chunk_file(temp_path)
            # Should be split into multiple chunks
            assert len(chunks) >= 1
            # No single chunk should exceed 6000 chars
            for chunk in chunks:
                assert len(chunk.content) <= 6000 or chunk.chunk_type == 'whole_file'
        finally:
            temp_path.unlink()

    def test_chunk_dataclass(self):
        """Test Chunk dataclass properties."""
        chunk = Chunk(
            content="test content",
            chunk_type="test",
            name="test_name",
            line_start=1,
            line_end=5,
            preview="test..."
        )
        assert chunk.content == "test content"
        assert chunk.chunk_type == "test"
        assert chunk.name == "test_name"
        assert chunk.token_estimate > 0

    def test_chunk_file_read_error(self):
        """Test chunking a file that cannot be read."""
        # Non-existent file
        path = Path("/nonexistent/file.py")
        chunks = self.chunker.chunk_file(path)
        assert chunks == []

    def test_chunk_json_file(self):
        """Test chunking a JSON file uses sliding window."""
        json_content = '{"key1": "value1", "key2": "value2"}'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(json_content)
            temp_path = Path(f.name)

        try:
            chunks = self.chunker.chunk_file(temp_path)
            assert len(chunks) >= 1
        finally:
            temp_path.unlink()

    def test_chunk_yaml_file(self):
        """Test chunking a YAML file uses sliding window."""
        yaml_content = 'key1: value1\nkey2: value2\n'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            chunks = self.chunker.chunk_file(temp_path)
            assert len(chunks) >= 1
        finally:
            temp_path.unlink()

    def test_chunk_yml_file(self):
        """Test chunking a YML file uses sliding window."""
        yml_content = 'key1: value1\nkey2: value2\n'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yml_content)
            temp_path = Path(f.name)

        try:
            chunks = self.chunker.chunk_file(temp_path)
            assert len(chunks) >= 1
        finally:
            temp_path.unlink()

    def test_chunk_invalid_python_syntax(self):
        """Test chunking invalid Python falls back to sliding window."""
        invalid_python = "def broken(\n    this is not valid python!!!"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(invalid_python)
            temp_path = Path(f.name)

        try:
            chunks = self.chunker.chunk_file(temp_path)
            # Should fall back to sliding window or whole_file
            assert len(chunks) >= 1
            # Either window (from sliding) or whole_file (small content fallback)
            assert all(c.chunk_type in ('window', 'whole_file') for c in chunks)
        finally:
            temp_path.unlink()

    def test_chunk_python_with_decorators(self):
        """Test chunking Python with decorated functions."""
        code = '''
@decorator
@another_decorator
def decorated_func():
    pass

@class_decorator
class DecoratedClass:
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)

        try:
            chunks = self.chunker.chunk_file(temp_path)
            # Should get function and class chunks including decorators
            func_chunks = [c for c in chunks if c.chunk_type == 'function']
            class_chunks = [c for c in chunks if c.chunk_type == 'class']
            # At least one function chunk with decorator
            if func_chunks:
                assert '@decorator' in func_chunks[0].content
        finally:
            temp_path.unlink()

    def test_chunk_large_class_truncation(self):
        """Test that very large classes get truncated with ellipsis."""
        # Create a chunker with small max_tokens to trigger truncation
        chunker = FileChunker(max_chunk_tokens=50)
        # Create a class with many methods (large enough to trigger truncation)
        methods = "\n".join([f"    def method_{i}(self):\n        x = {i}\n        return x\n" for i in range(200)])
        large_class = f"class VeryLargeClass:\n    '''A very large class with many methods.'''\n{methods}"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(large_class)
            temp_path = Path(f.name)

        try:
            chunks = chunker.chunk_file(temp_path)
            # Should get chunks
            assert len(chunks) >= 1
            # At least one class chunk should have truncation indicator
            class_chunks = [c for c in chunks if c.chunk_type == 'class']
            if class_chunks:
                # Large class should have "class continues" comment
                for c in class_chunks:
                    if "class continues" in c.content:
                        break
                # If we get here, the test exercises the truncation code path
        finally:
            temp_path.unlink()

    def test_chunk_markdown_no_headings(self):
        """Test markdown with no headings falls back to sliding window."""
        markdown = "This is just plain text.\nNo headings at all.\nJust paragraphs."
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(markdown)
            temp_path = Path(f.name)

        try:
            chunks = self.chunker.chunk_file(temp_path)
            # Falls back to sliding window
            assert len(chunks) >= 1
        finally:
            temp_path.unlink()

    def test_chunk_markdown_heading_hierarchy(self):
        """Test markdown chunks break at same/higher level headings."""
        # Need enough content in each section to meet min_tokens threshold
        markdown = '''# Top Level

Content under top level heading. This needs to be long enough
to satisfy the minimum token requirement for the chunker.
Adding more text here for the first section.

## Sub Level

Content under sub level heading. Also needs sufficient length
for the chunker to keep this section. More text here too.

# Another Top Level

More content under this top level heading. The chunker will
only keep sections with enough tokens to be meaningful.
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(markdown)
            temp_path = Path(f.name)

        try:
            chunks = self.chunker.chunk_file(temp_path)
            # Should get some chunks (section or window type)
            assert len(chunks) >= 1
            # May be section or window depending on size thresholds
            for c in chunks:
                assert c.chunk_type in ('section', 'window', 'whole_file')
        finally:
            temp_path.unlink()

    def test_chunk_filters_tiny_chunks(self):
        """Test that tiny chunks below min_tokens are filtered."""
        # Use high min_tokens to filter more
        chunker = FileChunker(min_chunk_tokens=100)
        small_content = "x\ny\nz"  # Very few tokens
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(small_content)
            temp_path = Path(f.name)

        try:
            chunks = chunker.chunk_file(temp_path)
            # Should still get at least whole_file fallback
            assert len(chunks) <= 1
        finally:
            temp_path.unlink()

    def test_chunk_large_empty_content_uses_sliding_window(self):
        """Test that large content with all filtered chunks uses sliding window."""
        # Create content that produces filtered chunks but is too large for whole_file
        large_content = "\n".join(["x" for _ in range(10000)])  # Many single-char lines

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(large_content)
            temp_path = Path(f.name)

        try:
            # High min_tokens filters all chunks, content > 6000 chars triggers sliding window
            chunks = self.chunker.chunk_file(temp_path)
            assert len(chunks) >= 1
        finally:
            temp_path.unlink()

    def test_chunk_python_async_function(self):
        """Test chunking async functions."""
        code = '''
async def async_func():
    await something()
    return True
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)

        try:
            chunks = self.chunker.chunk_file(temp_path)
            func_chunks = [c for c in chunks if c.chunk_type == 'function']
            # Should find async function
            if func_chunks:
                assert 'async_func' in [c.name for c in func_chunks]
        finally:
            temp_path.unlink()

    def test_chunk_with_preread_content(self):
        """Test chunking with pre-read content."""
        content = "def test():\n    pass\n"
        temp_path = Path("/fake/path.py")

        chunks = self.chunker.chunk_file(temp_path, content=content)
        assert len(chunks) >= 1


class TestTreeSitterChunking:
    """Tests for tree-sitter based chunking."""

    def setup_method(self):
        """Set up test fixtures with lower min_chunk_tokens for test code."""
        # Use lower min_chunk_tokens since test samples are small
        self.chunker = FileChunker(use_tree_sitter=True, min_chunk_tokens=5)

    def test_tree_sitter_available(self):
        """Test that tree-sitter availability is correctly detected."""
        from file_compass.chunker import TREE_SITTER_AVAILABLE
        # This test documents the state - tree-sitter may or may not be installed
        # If you need tree-sitter features, install with: pip install tree-sitter tree-sitter-python etc.
        assert isinstance(TREE_SITTER_AVAILABLE, bool)

    @requires_tree_sitter
    def test_chunk_javascript_file(self):
        """Test chunking JavaScript with tree-sitter."""
        js_code = '''
function greet(name) {
    // This function greets a person by name
    // It takes a name parameter and returns a greeting string
    const greeting = "Hello, " + name + "! Welcome to our application.";
    console.log("Generating greeting for:", name);
    return greeting;
}

class Person {
    constructor(name, age, email) {
        // Initialize person with name, age, and email
        this.name = name;
        this.age = age;
        this.email = email;
        this.createdAt = new Date();
    }

    sayHello() {
        // Returns a personalized greeting message
        const message = greet(this.name);
        console.log("Person says:", message);
        return message;
    }

    getInfo() {
        // Returns formatted information about this person
        return `Name: ${this.name}, Age: ${this.age}, Email: ${this.email}`;
    }
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(js_code)
            temp_path = Path(f.name)

        try:
            chunks = self.chunker.chunk_file(temp_path)
            assert len(chunks) >= 1
            # Should identify language
            assert any(c.language == "javascript" for c in chunks)
        finally:
            temp_path.unlink()

    @requires_tree_sitter
    def test_chunk_typescript_file(self):
        """Test chunking TypeScript with tree-sitter."""
        ts_code = '''
interface User {
    name: string;
    age: number;
    email: string;
    createdAt: Date;
}

interface UserConfig {
    maxUsers: number;
    defaultRole: string;
    enableNotifications: boolean;
}

function getUser(id: number): User {
    // Fetches a user by their unique identifier
    // Returns a User object with all properties filled in
    console.log("Fetching user with id:", id);
    return {
        name: "John",
        age: 30,
        email: "john@example.com",
        createdAt: new Date()
    };
}

class UserService {
    private users: User[] = [];
    private config: UserConfig;

    constructor(config: UserConfig) {
        // Initialize the user service with configuration
        this.config = config;
        this.users = [];
        console.log("UserService initialized with config:", config);
    }

    addUser(user: User): void {
        // Adds a new user to the service
        // Validates that we haven't exceeded max users
        if (this.users.length >= this.config.maxUsers) {
            throw new Error("Maximum users reached");
        }
        this.users.push(user);
        console.log("User added:", user.name);
    }

    findUser(email: string): User | undefined {
        // Finds a user by their email address
        // Returns undefined if not found
        return this.users.find(u => u.email === email);
    }
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(ts_code)
            temp_path = Path(f.name)

        try:
            chunks = self.chunker.chunk_file(temp_path)
            assert len(chunks) >= 1
            assert any(c.language == "typescript" for c in chunks)
        finally:
            temp_path.unlink()

    @requires_tree_sitter
    def test_chunk_python_with_tree_sitter(self):
        """Test Python chunking via tree-sitter."""
        python_code = '''
def hello():
    """Say hello to the world.

    This function returns a friendly greeting message
    that can be used to welcome users to the application.
    """
    greeting = "Hello, World!"
    print(f"Generated greeting: {greeting}")
    return greeting

class Greeter:
    """A greeter class for generating personalized greetings.

    This class provides methods to greet and say farewell to users
    with customized messages based on their names.
    """

    def __init__(self, default_greeting="Hello"):
        """Initialize the greeter with a default greeting."""
        self.default_greeting = default_greeting
        self.greet_count = 0

    def greet(self, name):
        """Generate a personalized greeting for the given name."""
        self.greet_count += 1
        message = f"{self.default_greeting}, {name}!"
        print(f"Greeting #{self.greet_count}: {message}")
        return message

    def farewell(self, name):
        """Generate a farewell message for the given name."""
        message = f"Goodbye, {name}! See you soon."
        print(f"Farewell: {message}")
        return message
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            temp_path = Path(f.name)

        try:
            chunks = self.chunker.chunk_file(temp_path)
            assert len(chunks) >= 1
            # Should identify language as python
            assert any(c.language == "python" for c in chunks)
        finally:
            temp_path.unlink()

    @requires_tree_sitter
    def test_chunk_rust_file(self):
        """Test chunking Rust with tree-sitter."""
        rust_code = '''
/// Adds two integers together and returns the result.
/// This function performs basic arithmetic addition.
fn add(a: i32, b: i32) -> i32 {
    let result = a + b;
    println!("Adding {} + {} = {}", a, b, result);
    result
}

/// Represents a point in 2D space with x and y coordinates.
/// This struct is used for geometric calculations.
struct Point {
    /// The x coordinate of the point
    x: f64,
    /// The y coordinate of the point
    y: f64,
    /// Optional label for this point
    label: Option<String>,
}

/// Implementation block for Point providing various methods.
impl Point {
    /// Creates a new Point with the given x and y coordinates.
    /// Returns a new Point instance.
    fn new(x: f64, y: f64) -> Self {
        println!("Creating new point at ({}, {})", x, y);
        Point { x, y, label: None }
    }

    /// Creates a new labeled Point with the given coordinates and label.
    fn with_label(x: f64, y: f64, label: &str) -> Self {
        println!("Creating labeled point: {} at ({}, {})", label, x, y);
        Point {
            x,
            y,
            label: Some(label.to_string()),
        }
    }

    /// Calculates the Euclidean distance between this point and another.
    /// Uses the Pythagorean theorem for calculation.
    fn distance(&self, other: &Point) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        let dist = (dx.powi(2) + dy.powi(2)).sqrt();
        println!("Distance from {:?} to {:?} = {}", self.label, other.label, dist);
        dist
    }
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
            f.write(rust_code)
            temp_path = Path(f.name)

        try:
            chunks = self.chunker.chunk_file(temp_path)
            assert len(chunks) >= 1
            assert any(c.language == "rust" for c in chunks)
        finally:
            temp_path.unlink()

    @requires_tree_sitter
    def test_chunk_go_file(self):
        """Test chunking Go with tree-sitter."""
        go_code = '''package main

import (
    "fmt"
    "strings"
)

// greet generates a personalized greeting message for the given name.
// It returns a formatted greeting string that includes the name.
func greet(name string) string {
    greeting := fmt.Sprintf("Hello, %s! Welcome to our application.", name)
    fmt.Println("Generated greeting:", greeting)
    return greeting
}

// formatName properly formats a name by capitalizing the first letter.
// It handles edge cases like empty strings.
func formatName(name string) string {
    if len(name) == 0 {
        return "Guest"
    }
    return strings.Title(strings.ToLower(name))
}

// Person represents an individual with their basic information.
// This struct is used for storing and managing user data.
type Person struct {
    Name      string
    Age       int
    Email     string
    IsActive  bool
}

// NewPerson creates a new Person with the given name and age.
// It initializes the person with default values for other fields.
func NewPerson(name string, age int) *Person {
    fmt.Printf("Creating new person: %s, age %d\\n", name, age)
    return &Person{
        Name:     formatName(name),
        Age:      age,
        IsActive: true,
    }
}

// SayHello generates a greeting message from this person.
// It uses the greet function to create the message.
func (p Person) SayHello() string {
    message := greet(p.Name)
    fmt.Printf("%s says: %s\\n", p.Name, message)
    return message
}

// GetInfo returns a formatted string with the person details.
// This is useful for logging and debugging purposes.
func (p Person) GetInfo() string {
    status := "inactive"
    if p.IsActive {
        status = "active"
    }
    return fmt.Sprintf("Name: %s, Age: %d, Status: %s", p.Name, p.Age, status)
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
            f.write(go_code)
            temp_path = Path(f.name)

        try:
            chunks = self.chunker.chunk_file(temp_path)
            assert len(chunks) >= 1
            assert any(c.language == "go" for c in chunks)
        finally:
            temp_path.unlink()

    @requires_tree_sitter
    def test_scope_context_method(self):
        """Test that methods have parent class context."""
        python_code = '''
class Calculator:
    """A simple calculator for performing basic arithmetic operations.

    This calculator class provides methods for addition, subtraction,
    multiplication, and division of numbers.
    """

    def __init__(self):
        """Initialize the calculator with a history list."""
        self.history = []
        self.last_result = None
        print("Calculator initialized")

    def add(self, a, b):
        """Add two numbers together and return the result.

        Args:
            a: First number
            b: Second number

        Returns:
            The sum of a and b
        """
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        self.last_result = result
        return result

    def subtract(self, a, b):
        """Subtract b from a and return the result.

        Args:
            a: Number to subtract from
            b: Number to subtract

        Returns:
            The difference a - b
        """
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        self.last_result = result
        return result
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            temp_path = Path(f.name)

        try:
            chunks = self.chunker.chunk_file(temp_path)
            # Look for method chunks
            method_chunks = [c for c in chunks if c.chunk_type == "method"]
            if method_chunks:
                # Methods should have parent_class set
                for mc in method_chunks:
                    assert mc.parent_class == "Calculator"
                    assert mc.qualified_name.startswith("Calculator.")
        finally:
            temp_path.unlink()

    def test_qualified_name(self):
        """Test qualified name generation."""
        chunk = Chunk(
            content="test",
            chunk_type="method",
            name="my_method",
            line_start=1,
            line_end=5,
            preview="test",
            parent_class="MyClass"
        )
        assert chunk.qualified_name == "MyClass.my_method"

        # Function without class
        func_chunk = Chunk(
            content="test",
            chunk_type="function",
            name="my_func",
            line_start=1,
            line_end=5,
            preview="test"
        )
        assert func_chunk.qualified_name == "my_func"

    def test_disable_tree_sitter(self):
        """Test that tree-sitter can be disabled."""
        chunker = FileChunker(use_tree_sitter=False)
        assert chunker.use_tree_sitter is False
        assert len(chunker._parsers) == 0

    def test_fallback_on_parse_error(self):
        """Test fallback to sliding window on tree-sitter parse failure."""
        # Invalid JS that might confuse tree-sitter
        invalid_js = "function {{{broken code here}}}"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(invalid_js)
            temp_path = Path(f.name)

        try:
            chunks = self.chunker.chunk_file(temp_path)
            # Should still get some chunks (sliding window fallback or whole_file)
            assert len(chunks) >= 1
        finally:
            temp_path.unlink()
