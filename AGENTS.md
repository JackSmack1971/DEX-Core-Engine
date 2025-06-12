**1. Overall Principles**
*   **Prioritize Readability:** Write code that is easy for humans to understand, as code is read much more often than it is written.
*   **Be Consistent:** Maintain consistency within your project, and especially within a module or function. Know when to deviate from general guidelines if it makes the code less readable or to maintain backward compatibility.
*   **Follow Established Standards:** Adhere to common guidelines like PEP 8 to ensure uniformity and reduce errors, as much code out there follows it.
*   **Practice "Broken Windows" Theory:** Immediately repair bugs and defects rather than postponing them, as putting them off can lead to more complex problems later.
*   **Embrace Pythonic Idioms:** Use Python’s idiomatic ways of writing code, which are often more readable and efficient.
*   **Balance Trade-offs:** Understand that conflicts between different code quality characteristics (e.g., readability vs. efficiency) are common; prioritize based on specific project requirements, team skills, and context.

**2. Code Style & Readability**
*   **Indentation:** Use 4 spaces per indentation level consistently. For continuation lines, align wrapped elements vertically or use a hanging indent without arguments on the first line.
*   **Line Length:** Limit all lines to a maximum of 79 characters, and 72 characters for docstrings and comments. Break long lines using Python’s implicit line joining inside parentheses, brackets, or braces, preferring breaks before binary operators for new code.
*   **Naming Conventions:**
    *   **Be Descriptive:** Use clear, descriptive names for all code entities (variables, functions, methods, classes, modules, constants). Avoid abbreviations, single-letter names (except for specific, clear contexts like loop counters), and redundant labeling.
    *   **Style Guidelines:** Adopt `lower_case_with_underscores` for variables, functions, methods, packages, and modules. Use `CapWords` for class names and exception names (with an "Error" suffix if an error). Use `ALL_CAPS_WITH_UNDERSCORES` for constants.
    *   **Internal Elements:** Prefix internal or non-public elements with a single underscore (`_single_leading_underscore`). Avoid using double leading underscores (`__double_leading_underscore`) for general privacy, as it impacts readability and testability.
    *   **Arguments:** Use `self` for the first argument to instance methods and `cls` for class methods. If an argument name clashes with a reserved keyword, append a single trailing underscore (e.g., `class_`).
*   **Whitespace:** Use blank lines to separate top-level function and class definitions (two lines) and method definitions inside a class (one line). Use single spaces around binary operators (assignment, comparisons, Booleans) and after commas. Avoid extraneous whitespace immediately inside parentheses, brackets, or braces, or before commas, semicolons, or colons. Avoid trailing whitespace.
*   **Strings:** Be consistent with your choice of single or double quotes within a file. Use the alternative quote style to avoid backslashes when the string contains quotes. Prefer triple double-quotes (`"""`) for multiline strings and docstrings.
*   **One Statement Per Line:** Generally, avoid putting multiple disjointed statements on the same line.
*   **Boolean Comparisons:** Do not compare boolean values directly to `True` or `False` using `==` or `is`. Instead, rely on Python's implicit boolean evaluation (e.g., `if greeting:`). Always use `is` or `is not` when comparing to singletons like `None`.
*   **List Manipulations:** Use list comprehensions or generator expressions for creating and filtering lists efficiently and concisely. For large datasets, prefer generator expressions over list comprehensions to save memory. Never remove items from a list while iterating over it. Use `str.join()` for creating strings from lists efficiently.
*   **File Handling:** Use the `with open` syntax to ensure files are automatically and promptly closed, even if exceptions occur. Use `contextlib.closing()` for file-like objects that don't support `with` statements directly.

**3. Modular Design & Structure**
*   **Modularize Codebase:** Break down your software into smaller, manageable, and reusable pieces or modules, with each handling a specific part of the program. Organize code into directories and files that reflect this modular structure.
*   **Single Responsibility Principle (SRP):** Design each module, class, or function to have only one reason to change, focusing on a single, well-defined task.
*   **High Cohesion:** Ensure that the functions and elements within a module are closely related and work together to achieve a common goal.
*   **Low Coupling:** Design modules to be independent of each other, with minimal interaction, typically communicating through well-defined interfaces. This reduces the risk of changes in one module affecting others.
*   **Encapsulation:** Hide the internal details of a module and expose only what is necessary for other modules to interact with it, using public methods and properties.
*   **DRY Principle (Don’t Repeat Yourself):** Avoid duplicating code. If you find yourself writing the same code more than once, refactor it into reusable modules, functions, or classes.
*   **Define Module Boundaries:** Clearly identify and define logical boundaries between different parts of your application based on core functionalities, adhering to SRP and high cohesion.
*   **Use Interfaces and Abstractions:** Define the behavior of a module through interfaces and abstractions without specifying implementation details. This promotes low coupling and makes modules more flexible and replaceable.
*   **Implement Dependency Injection:** Manage dependencies between modules by passing them as parameters or using dependency injection frameworks, making modules more flexible and easier to test.
*   **Small and Focused Functions:** Prefer small and focused functions. If a function exceeds approximately 40 lines, consider breaking it into smaller, more manageable pieces to enhance readability and maintainability.
*   **Avoid Circular Dependencies:** Design your modules carefully to prevent direct or indirect mutual dependencies, which can complicate understanding and maintenance.

**4. Error Handling**
*   **Use Try-Except Blocks:** Enclose code that might raise an exception within a `try` block and follow it with an `except` block to gracefully catch and handle the exception, preventing unexpected program crashes.
*   **Provide Informative Error Messages:** When an error occurs, ensure your error messages are clear, helpful, explain what went wrong, and, if possible, suggest how to fix it.
*   **Use Custom Exceptions:** For more specific error conditions, define custom exception classes that inherit from the built-in `Exception` class.
*   **Catch Specific Exceptions:** Avoid using bare `except:` clauses; instead, catch specific exceptions whenever possible to prevent masking other problems and unintended behavior. Limit the code within a `try` clause to the absolute minimum necessary to avoid hiding bugs.
*   **Consistent Return Statements:** Ensure all return statements in a function are consistent. Either all return an expression, or none do. If any return an expression, others should explicitly `return None`, and an explicit `return` statement should be present at the end if reachable.

**5. Efficiency & Performance**
*   **Optimize Code:** Aim to write code that performs well, especially for crucial or frequently run tasks, by choosing faster algorithms and reducing time complexity (e.g., using list comprehensions can be faster than traditional loops for simple operations).
*   **Appropriate Data Structures:** Select the right data structure, as it can significantly impact performance (e.g., use sets for faster membership tests than lists for large data).
*   **Profile Code:** Use profiling tools like `cProfile`, `timeit`, `perf`, `py-spy`, or `Scalene` to identify performance bottlenecks, high CPU/memory usage, and inefficient algorithms, allowing you to focus optimization efforts where they have the most impact.
*   **Avoid Unnecessary Computations:** Minimize redundant calculations by storing and reusing results of expensive operations if they are needed multiple times.
*   **Leverage Built-in Functions and Libraries:** Use Python’s standard library and built-in functions (e.g., `max()`, `sum()`) instead of writing custom code to save time and reduce the likelihood of errors.
*   **Scalability:** Design code to handle increasing workloads, data sizes, or user demands without compromising performance, stability, or maintainability. Use generator expressions for large data to save memory compared to creating full lists.

**6. Testing**
*   **Write Unit Tests:** Crucial for verifying code functionality, ensuring correctness, and preventing regressions when changes are made.
*   **Use Testing Frameworks:** Utilize Python’s built-in `unittest` module or third-party frameworks like `pytest`.
*   **Test Isolation:** Ensure tests are isolated and do not interact with real external resources like databases or networks. Use separate test databases or mock objects.
*   **Descriptive Test Names:** Use long, descriptive names for test methods and classes. For functional tests, write test case and method names that read like a scenario description.
*   **Fast Tests:** Unit tests should be fast, but a slow test is still better than no test.
*   **Avoid Incomplete Tests:** Never let incomplete tests pass; add explicit placeholders like `assert False, "TODO: finish me"` to ensure they are addressed.
*   **Test-Driven Development (TDD):** Consider beginning development by writing tests based on requirements, then implementing the code to pass those tests.
*   **Make Code Testable:** Design functions to return concrete results rather than relying on side effects (e.g., printing directly) to simplify automated testing.

**7. Documentation**
*   **Write Docstrings:** Document all public modules, functions, classes, and methods immediately after their definition. Docstrings should clearly explain the purpose, parameters, and return values. Use triple double-quotes (`"""`) for all docstrings, with a summary line on the first line.
*   **Meaningful Comments:** Use comments sparingly, focusing on explaining *why* something is done rather than merely *what* the code does. Keep comments clear, concise, complete, and up-to-date with code changes. Write comments in English.
*   **Document Public Interfaces:** Clearly document the input parameters, output, and source for methods and functions that are intended for use by other parts of the system or other developers, without delving into implementation details.
*   **Use README Files:** Provide essential project information, such as setup instructions, usage examples, and purpose, in a `README` file in the root directory of your project.
*   **TODO Comments:** Use a specific format for `TODO` comments (`# TODO: <link_to_resource> - <explanatory_string>`) to denote temporary solutions or future tasks, ideally linking to a bug tracker or specific event.

**8. Security**
*   **Validate User Input:** Always validate user input to prevent security vulnerabilities, such as unexpected data types, out-of-range values, or malicious injections, which can lead to crashes or incorrect behavior.
*   **Avoid Risky Constructs:** Be cautious when using functions like `exec()`, `eval()`, and `pickle.load()`, as they can introduce security risks if not handled with extreme care.
*   **Vulnerability Checkers:** Use security-focused linters and tools like `Bandit` to scan your code for common vulnerabilities and insecure coding patterns.

**9. Tools & Automation**
*   **Code Linters:** Use tools like `Pylint`, `Flake8`, and `Ruff` to analyze your code for potential errors, code smells, and adherence to coding style guides like PEP 8. Integrate these tools into your IDE to get real-time feedback.
*   **Code Formatters:** Employ tools such as `Black`, `Isort`, `Ruff`, and `autopep8` to automatically format your code consistently according to accepted coding styles (e.g., PEP 8). Configure your IDE to run formatters automatically on save to minimize manual formatting efforts.
*   **Static Type Checkers:** Use tools like `mypy` or `Pyright` to validate type annotations (type hints) in your code and catch type-related bugs before runtime, improving code correctness and maintainability.
*   **Virtual Environments:** Use virtual environments (e.g., `venv`) to manage project dependencies on a per-project basis, preventing conflicts between packages used in different projects and ensuring reproducibility.
*   **AI Assistants:** Leverage AI tools (e.g., ChatGPT, Real Python Code Mentor, Copilot) as assistants to generate, review, improve, extend, document, and test your code, helping to identify and fix errors, ensure style compliance, and optimize performance.
*   **Pre-commit Hooks:** Integrate automated quality checks (such as linters, formatters, and tests) into your version control system’s pre-commit hooks. This enforces code quality standards before code is even committed or merged, preventing low-quality code from entering the codebase.

**10. Collaboration & Maintenance**
*   **Code Reviews:** Regularly conduct code reviews, where you examine and evaluate each other’s code to ensure it meets quality standards, verify correctness, improve clarity, promote modular design, ensure proper error handling, confirm adherence to style guidelines, and detect vulnerabilities.
*   **Version Control:** Use version control systems like Git to manage changes to your codebase, facilitate collaboration with other agents, and track the history of your modules. Use meaningful commit messages.
*   **Regular Refactoring:** Continuously improve your code’s structure, readability, and maintainability without altering its external functionality. This helps keep modules clean and reduces technical debt over time.
*   **Acquaintance with PyPI:** Get familiar with PyPI (The Python Package Index), a collective repository for thousands of Python projects. Utilize existing projects and modules from PyPI to avoid reinventing the wheel and to leverage well-tested, high-quality code.