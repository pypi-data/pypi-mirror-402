![RUNTIME banner](images/banner.png)

**RUNTIME is a complete reimagining of what a programming language could and should be.**

RUNTIME is a dynamic, interpreted language that removes the boundaries between data and code.

No type cages. No compile-time errors. No bloat. Just you, your ideas and a blank canvas.

> **ABOUT AI USAGE:** I have used AI to rewrite some parts of this README and for general design guidance. AI hasn't written a single line of code for this project.

# NAVIGATION

- [PHILOSOPHY - The 6 Core Pillars of RUNTIME](#philosophy---the-6-core-pillars-of-runtime)
    - [Typed languages are cages](#typed-languages-are-cages)
    - [Variables are memory entries](#variables-are-memory-entries)
    - [Code is text](#code-is-text)
    - [Programs should evolve](#programs-should-evolve)
    - [Errors are values](#errors-are-values)
    - [Simplicity is key](#simplicity-is-key)
- [USE CASES](#use-cases)
    - [Examples](#examples)
        - [1. Code is text](#1-code-is-text)
        - [2. Dynamic variables](#2-dynamic-variables)
        - [3. Hot-swapping built-ins](#3-hot-swapping-built-ins)
        - [4. AI written features](#4-ai-written-features)
- [GETTING STARTED](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Usage](#usage)
    - [Resources](#resources)

# PHILOSOPHY - The 6 Core Pillars of RUNTIME

> **DISCLAIMER:** RUNTIME is in active development and not all features described in the philosophy are available as of now.

### Typed languages are cages

Typed, compiled languages promise "safety", but all they do is get in your way. Type mismatches, rigid syntax and compile-time errors kill your ideas before they even start. In RUNTIME, stuff just RUNS. With no rules and no types, you can focus on ACTUALLY CODING and bringing your raw, unfiltered ideas to life.

### Variables are memory entries

Variables and functions are just named memory entries. So why do most languages treat them like sacred artifacts? In RUNTIME, names are flexible. You can construct them, change them or pass them around, just like ANY OTHER VALUE.

### Code is text

When you're writing code, you're writing text. So why do most languages act like code and text are completely separate worlds? In RUNTIME, they're the same thing. Code is data and data is code. Want to store functions in plain text? Generate logic on the fly? Rewrite your code while it runs? Go for it.

### Programs should evolve

Other languages treat your program like a dead script: once it runs, it’s frozen. But that’s not how humans think. With RUNTIME, your program is alive. You can interact with the interpreter, redefine built-ins, and mutate your logic while it runs. Handle bugs. Inject new features. Adapt and evolve.

### Errors are values

Make one typo and your whole app explodes? That's a JOKE. In RUNTIME, errors are values. They don’t crash your program, they just show up, like ANY OTHER RESULT. You can inspect them, log them, ignore them, or react to them. Your code keeps going.

### Simplicity is key

> **An idiot admires complexity, a genius admires simplicity**
>
> — Terry Davis, creator of TempleOS

Tuples, arrays, lists, stacks, queues... WHY? RUNTIME gives you just 7 types. No bloat. No confusion. No distractions. Still, all the tools you need to ACTUALLY bring your projects to life.

# USE CASES

-   **Self-modifying programs**: AI written on-demand features? Self-evolving code? You can do that and much more.
-   **Self-debugging code**: Instead of crashing on errors, your program can patch itself and keep going.
-   **Hot-swappable features**: Replace or generate entire functions and modules at runtime. No restarts required.

## Examples

### 1. Code is text <small>(code_is_text.run)</small>

```javascript
code = "print({ Hello from text! })"
code() // Executes the text object as code

// > Hello from text!
```

### 2. Dynamic variables <small>(dynamic_variables.run)</small>

```javascript
make_variable = {
    name = arguments[0]
    value = arguments[1]

    [1]$(name) = value

    // [1] references the parent scope
    // $ starts the variable assignment
    // (name) is a dynamic variable name
}

make_variable("message", "Hello world!")
print(message) // > Hello world!
```

### 3. Hot-swapping built-ins <small>(hot_swapping_built_ins.run)</small>

```javascript
// Overwrite print to add a prefix
print = {
    [default]print("LOG: " + arguments[0])
}

print("Hello World!") // > LOG: Hello World!

// Restore default
print = [default]print // Get function from default scope
print("Back to normal!") // > Back to normal!
```


### 4. AI written features <small>(ai_written_features.run)</small>

```javascript
while (true) {
    request = input("INPUT (execute | add feature): ").strip().to_lowercase()

    if (request == "execute") 
    {
        feature = input("What feature should I execute? ")
        $(feature)() // Execute a function from a dynamic name
    } 
    else if (request == "add feature") 
    {
        // Request a feature and ask AI to code it
        feature = input("What feature should I add? ")
        code = ai.vibecode(feature + "\n\nOutput a function only.")

        print(); print("AI wrote the following code:")
        print(); print(code)
        
        code = "[global]" + code // Declare the function in the global scope
        (code)() // Execute the code

        print(); print("Feature added! Try running it now.")
    }

    print()
}
```

![Example image](images/example.png)

# GETTING STARTED

## Prerequisites

- [Python 3.12 or greater](https://www.python.org/downloads/)

## Installation

```bash
pip install runtime-lang
```

## Usage

- Run `ai_written_features.run` from the examples
    
    ```bash
    runtime ai_written_features
    ```
    or
    ```bash
    runtime ai_written_features.run
    ```

- Run `my_program.run` in the current directory

    ```bash
    runtime my_program
    ```
    or
    ```bash
    runtime my_program.run
    ```

- Start REPL

    ```bash 
    runtime
    ```

## Resources

- [RUNTIME Guide](https://github.com/Mikuel210/RUNTIME/blob/main/GUIDE.md)
- [RUNTIME Documentation](https://github.com/Mikuel210/RUNTIME/blob/main/DOCUMENTATION.md)


---

RUNTIME isn't just a new language.

**It's a new way to think.**
