import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models.skill import Skill
from models.mastery import Mastery
from models.diagnostic import DiagnosticQuestion

logger = logging.getLogger("apogee.diagnostic_service")


def get_verification_questions_for_skill(skill_name: str, skill_slug: str = "") -> List[Dict[str, Any]]:
    """
    Returns exactly 5 multiple-choice verification questions for a skill.
    Correct answers (correct_index) are stored server-side only — never sent to frontend.
    """
    sn = skill_name.lower()

    if "html" in sn or "css" in sn:
        return [
            {"question": "Which HTML element is recommended for main navigation links?",
             "options": ["<nav>", "<div>", "<section>", "<header>"],
             "correct_index": 0, "explanation": "The semantic <nav> tag specifies a navigation section."},
            {"question": "In CSS Flexbox, which property aligns items along the main axis?",
             "options": ["align-items", "justify-content", "place-content", "flex-direction"],
             "correct_index": 1, "explanation": "justify-content aligns items on the main axis."},
            {"question": "What does `box-sizing: border-box` do?",
             "options": ["Adds a visible box border", "Includes padding and border in the element's total width/height",
                         "Creates a shadow around the box", "Enables flex layout"],
             "correct_index": 1, "explanation": "border-box makes width/height include padding and border."},
            {"question": "Which CSS selector targets direct children only?",
             "options": ["div p", "div > p", "div + p", "div ~ p"],
             "correct_index": 1, "explanation": "The > combinator selects direct children."},
            {"question": "What is the correct HTML5 doctype declaration?",
             "options": ["<!DOCTYPE HTML PUBLIC>", "<!DOCTYPE html>", "<html doctype='5'>", "<?xml version='1.0'?>"],
             "correct_index": 1, "explanation": "<!DOCTYPE html> is the HTML5 doctype."},
        ]
    elif "javascript" in sn or " js" in sn or "es6" in sn:
        return [
            {"question": "What does `typeof NaN` return in JavaScript?",
             "options": ['"number"', '"nan"', '"undefined"', '"object"'],
             "correct_index": 0, "explanation": "NaN has type 'number' in JavaScript."},
            {"question": "Which array method creates a new array with transformed elements?",
             "options": ["forEach()", "map()", "filter()", "reduce()"],
             "correct_index": 1, "explanation": "map() returns a new array with each element transformed."},
            {"question": "What is the output of `[] == false` in JavaScript?",
             "options": ["false", "true", "TypeError", "undefined"],
             "correct_index": 1, "explanation": "Due to type coercion, [] coerces to 0 and false to 0, so they are equal."},
            {"question": "Which keyword declares a block-scoped variable in ES6?",
             "options": ["var", "let", "def", "scope"],
             "correct_index": 1, "explanation": "let is block-scoped unlike var which is function-scoped."},
            {"question": "What does the spread operator `...` do when used with an array?",
             "options": ["Deletes array elements", "Expands array elements into individual arguments",
                         "Sorts the array", "Creates a deep clone"],
             "correct_index": 1, "explanation": "The spread operator expands an iterable into individual elements."},
        ]
    elif "react" in sn:
        return [
            {"question": "Which hook handles side-effects in React functional components?",
             "options": ["useState", "useEffect", "useMemo", "useCallback"],
             "correct_index": 1, "explanation": "useEffect handles side effects like data fetching or subscriptions."},
            {"question": "What is the primary purpose of keys in React lists?",
             "options": ["To style list items", "To help React identify changed/added/removed items",
                         "To count array items", "To trigger state updates"],
             "correct_index": 1, "explanation": "Keys give React elements a stable identity for efficient reconciliation."},
            {"question": "What does `useState` return?",
             "options": ["The current state only", "A state value and a setter function", "A ref object", "A context"],
             "correct_index": 1, "explanation": "useState returns [state, setState] — the current value and its updater."},
            {"question": "When does a React component re-render?",
             "options": ["Only when the DOM changes", "When its state or props change", "When any variable changes", "Every second"],
             "correct_index": 1, "explanation": "React re-renders when state or props change."},
            {"question": "Which React concept allows passing data without prop drilling?",
             "options": ["Portals", "Context API", "Refs", "Fragments"],
             "correct_index": 1, "explanation": "Context API provides a way to share values without explicit prop drilling."},
        ]
    elif "typescript" in sn or " ts" in sn:
        return [
            {"question": "Which TypeScript utility type makes all properties optional?",
             "options": ["Required<T>", "Partial<T>", "Readonly<T>", "Pick<T>"],
             "correct_index": 1, "explanation": "Partial<T> makes all properties of T optional."},
            {"question": "What does the `unknown` type mean in TypeScript?",
             "options": ["Same as any", "A type-safe counterpart of any that requires type narrowing before use",
                         "A runtime error", "An unresolved import"],
             "correct_index": 1, "explanation": "unknown is like any but forces type checking before operations."},
            {"question": "What is a TypeScript interface used for?",
             "options": ["Implementing a class", "Describing the shape of an object", "Declaring a variable", "Importing modules"],
             "correct_index": 1, "explanation": "Interfaces define contracts for object shapes."},
            {"question": "What does `as const` do in TypeScript?",
             "options": ["Creates a constant function", "Infers the most specific literal types",
                         "Declares a class constant", "Disables type checking"],
             "correct_index": 1, "explanation": "as const makes TypeScript infer literal types instead of widening."},
            {"question": "Which TypeScript feature allows a variable to hold multiple types?",
             "options": ["Generics", "Union Types", "Enums", "Namespaces"],
             "correct_index": 1, "explanation": "Union types (A | B) allow a value to be one of several types."},
        ]
    elif "state" in sn and ("mgmt" in sn or "management" in sn or "redux" in sn):
        return [
            {"question": "What is the Redux single source of truth principle?",
             "options": ["Each component has its own store", "The whole app state is in one store",
                         "State lives in the database", "Reducers hold state locally"],
             "correct_index": 1, "explanation": "Redux stores the entire app state in a single store."},
            {"question": "What is a Redux reducer?",
             "options": ["A component that renders data", "A pure function that takes state + action and returns new state",
                         "A middleware function", "A database query"],
             "correct_index": 1, "explanation": "Reducers are pure functions specifying how state changes in response to actions."},
            {"question": "In Redux, what does dispatching an action do?",
             "options": ["Renders a component", "Sends the action to the reducer to produce new state",
                         "Fetches data from an API", "Unmounts a component"],
             "correct_index": 1, "explanation": "Dispatching sends an action object through the Redux middleware chain to the reducer."},
            {"question": "What is the purpose of Redux middleware like redux-thunk?",
             "options": ["To render async UI", "To handle async logic before actions reach the reducer",
                         "To replace reducers", "To cache API responses"],
             "correct_index": 1, "explanation": "Thunk middleware lets you write action creators that return functions for async operations."},
            {"question": "Which Redux Toolkit function creates a slice of state with reducer and actions?",
             "options": ["createReducer()", "createSlice()", "createSelector()", "createStore()"],
             "correct_index": 1, "explanation": "createSlice() generates action creators and a reducer from a single configuration."},
        ]
    elif "test" in sn and ("frontend" in sn or "jest" in sn or "rtl" in sn):
        return [
            {"question": "What does `render()` from React Testing Library return?",
             "options": ["A DOM string", "Utility functions to query the rendered component", "A React component class", "A snapshot"],
             "correct_index": 1, "explanation": "render() returns query utilities like getByText, getByRole, etc."},
            {"question": "Which Testing Library query is preferred for accessibility?",
             "options": ["getByClassName", "getByRole", "getByTagName", "getByStyle"],
             "correct_index": 1, "explanation": "getByRole queries by ARIA role, encouraging accessible markup."},
            {"question": "What does `jest.fn()` create?",
             "options": ["A test suite", "A mock function that records calls", "A snapshot", "An async runner"],
             "correct_index": 1, "explanation": "jest.fn() creates a mock function you can assert against."},
            {"question": "What is the purpose of `act()` in React Testing Library?",
             "options": ["To render components", "To ensure all state updates and effects are processed before assertions",
                         "To mock APIs", "To create snapshots"],
             "correct_index": 1, "explanation": "act() wraps code that causes React state updates to flush before assertions."},
            {"question": "What does a snapshot test verify?",
             "options": ["API response speed", "That rendered output matches a previously saved snapshot",
                         "Database schema", "Network requests"],
             "correct_index": 1, "explanation": "Snapshot tests catch unintended UI changes by comparing against saved output."},
        ]
    elif "python" in sn:
        return [
            {"question": "Which Python data structure is mutable?",
             "options": ["Tuple", "List", "String", "Frozenset"],
             "correct_index": 1, "explanation": "Lists are mutable; tuples, strings, and frozensets are immutable."},
            {"question": "What does `pass` do in Python?",
             "options": ["Terminates the function", "Acts as a null syntax placeholder", "Skips to next iteration", "Raises SyntaxError"],
             "correct_index": 1, "explanation": "pass is a null operation used as a placeholder."},
            {"question": "What is a Python decorator?",
             "options": ["A CSS-like style", "A function that wraps another function to modify its behavior",
                         "A type annotation", "A list comprehension"],
             "correct_index": 1, "explanation": "Decorators wrap functions to extend or modify their behavior without changing the source."},
            {"question": "What does `*args` do in a Python function definition?",
             "options": ["Unpacks a dictionary", "Allows any number of positional arguments", "Creates a generator", "Raises TypeError"],
             "correct_index": 1, "explanation": "*args collects extra positional arguments into a tuple."},
            {"question": "Which statement is used to handle exceptions in Python?",
             "options": ["catch/throw", "try/except", "error/handle", "begin/rescue"],
             "correct_index": 1, "explanation": "Python uses try/except blocks for exception handling."},
        ]
    elif "math" in sn or "stats" in sn or "linear" in sn or "algebra" in sn:
        return [
            {"question": "What is the result of multiplying a 3×2 matrix by a 2×4 matrix?",
             "options": ["3×4 matrix", "2×2 matrix", "3×2 matrix", "Cannot be multiplied"],
             "correct_index": 0, "explanation": "The result has dimensions (rows of A) × (cols of B) = 3×4."},
            {"question": "Which metric measures spread of data relative to its mean?",
             "options": ["Median", "Standard Deviation", "Mode", "Quantile"],
             "correct_index": 1, "explanation": "Standard deviation measures dispersion around the mean."},
            {"question": "What is the dot product of [1,2,3] and [4,5,6]?",
             "options": ["15", "32", "21", "12"],
             "correct_index": 1, "explanation": "1×4 + 2×5 + 3×6 = 4+10+18 = 32."},
            {"question": "In probability, what must all outcomes in a sample space sum to?",
             "options": ["0", "1", "100", "Infinity"],
             "correct_index": 1, "explanation": "All probabilities in a sample space must sum to 1."},
            {"question": "What does the gradient of a function indicate?",
             "options": ["The average value", "The direction and rate of steepest ascent",
                         "The area under the curve", "The function's roots"],
             "correct_index": 1, "explanation": "The gradient points in the direction of greatest increase."},
        ]
    elif "data" in sn or "pandas" in sn or "numpy" in sn or "analysis" in sn:
        return [
            {"question": "Which Pandas method removes rows with missing values?",
             "options": ["fillna()", "dropna()", "isna()", "drop_duplicates()"],
             "correct_index": 1, "explanation": "dropna() removes rows or columns containing NaN values."},
            {"question": "What is the main advantage of NumPy arrays over Python lists?",
             "options": ["Dynamic typing", "Vectorized contiguous memory operations", "Auto DB syncing", "Thread safety"],
             "correct_index": 1, "explanation": "NumPy arrays use contiguous C-memory for fast vectorized math."},
            {"question": "Which Pandas operation combines DataFrames based on a common column?",
             "options": ["concat()", "merge()", "append()", "pivot()"],
             "correct_index": 1, "explanation": "merge() joins DataFrames like SQL JOIN on common columns."},
            {"question": "What does `df.groupby('col').mean()` compute?",
             "options": ["Total sum per group", "Mean of each group for all columns", "Count per group", "Standard deviation"],
             "correct_index": 1, "explanation": "groupby().mean() computes the mean of each numerical column within each group."},
            {"question": "What does `df.describe()` return?",
             "options": ["Column names", "Summary statistics (count, mean, std, min, max, quartiles)",
                         "Missing value count", "Data types"],
             "correct_index": 1, "explanation": "describe() gives a statistical summary of numeric columns."},
        ]
    elif "scikit" in sn or "supervised" in sn or "machine learning" in sn:
        return [
            {"question": "What does train/test split prevent?",
             "options": ["Underfitting", "Overfitting on training data evaluated on unseen data", "Missing data", "Feature scaling"],
             "correct_index": 1, "explanation": "Splitting reserves unseen data to evaluate true generalization."},
            {"question": "Which sklearn function scales features to zero mean and unit variance?",
             "options": ["MinMaxScaler", "StandardScaler", "RobustScaler", "Normalizer"],
             "correct_index": 1, "explanation": "StandardScaler standardizes by removing mean and scaling to unit variance."},
            {"question": "What metric measures the fraction of correctly classified samples?",
             "options": ["Precision", "Accuracy", "Recall", "F1-score"],
             "correct_index": 1, "explanation": "Accuracy = correct predictions / total predictions."},
            {"question": "Which algorithm is used for dimensionality reduction in sklearn?",
             "options": ["KMeans", "PCA", "SVM", "RandomForest"],
             "correct_index": 1, "explanation": "PCA (Principal Component Analysis) reduces dimensions while preserving variance."},
            {"question": "What does cross-validation do?",
             "options": ["Validates CSS", "Evaluates model performance across multiple data splits",
                         "Checks database integrity", "Encrypts model weights"],
             "correct_index": 1, "explanation": "Cross-validation gives a more robust estimate of model performance."},
        ]
    elif "deep learning" in sn or "pytorch" in sn or "tensorflow" in sn or "neural" in sn:
        return [
            {"question": "What is the purpose of an activation function in a neural network?",
             "options": ["To store weights", "To introduce non-linearity", "To normalize inputs", "To count layers"],
             "correct_index": 1, "explanation": "Activation functions add non-linearity, enabling networks to learn complex patterns."},
            {"question": "What does backpropagation compute?",
             "options": ["Forward pass output", "Gradients of the loss with respect to each weight",
                         "The number of epochs", "Dropout masks"],
             "correct_index": 1, "explanation": "Backprop uses the chain rule to compute gradients for weight updates."},
            {"question": "What is overfitting in deep learning?",
             "options": ["Model performs poorly on training data", "Model performs well on training data but poorly on unseen data",
                         "Model is too shallow", "Loss is not decreasing"],
             "correct_index": 1, "explanation": "Overfitting occurs when a model memorizes training data instead of generalizing."},
            {"question": "Which technique randomly deactivates neurons during training?",
             "options": ["Batch Normalization", "Dropout", "L2 Regularization", "Learning Rate Decay"],
             "correct_index": 1, "explanation": "Dropout randomly zeros neurons to prevent co-adaptation and overfitting."},
            {"question": "In PyTorch, which call computes gradients?",
             "options": ["optimizer.step()", "loss.backward()", "model.forward()", "torch.grad()"],
             "correct_index": 1, "explanation": "loss.backward() triggers backpropagation and populates .grad attributes."},
        ]
    else:
        # Generic 5-question fallback
        return [
            {"question": f"What is a core prerequisite concept in {skill_name}?",
             "options": ["Syntax & Fundamentals", "Advanced Optimization", "Database Indexing", "Container Deployment"],
             "correct_index": 0, "explanation": f"Understanding syntax and core primitives is essential for {skill_name}."},
            {"question": f"Which best practice applies when applying {skill_name} in production?",
             "options": ["Hardcode credentials", "Modular structured clean code", "Ignore exception handling", "Disable logging"],
             "correct_index": 1, "explanation": "Modular code with robust error handling ensures production reliability."},
            {"question": f"What does debugging {skill_name} code typically involve?",
             "options": ["Random changes", "Systematic isolation and reproduction of issues",
                         "Deleting the codebase", "Rewriting from scratch"],
             "correct_index": 1, "explanation": "Debugging requires systematic isolation to reproduce and fix root causes."},
            {"question": f"Which tool is most associated with testing in {skill_name}?",
             "options": ["A spreadsheet", "Automated test frameworks", "Manual code review only", "Database triggers"],
             "correct_index": 1, "explanation": "Automated tests catch regressions and confirm expected behavior."},
            {"question": f"How does version control help when working with {skill_name}?",
             "options": ["It stores database records", "It tracks changes, enables collaboration, and supports rollback",
                         "It deploys to production", "It speeds up compilation"],
             "correct_index": 1, "explanation": "Version control is essential for tracking changes and collaborating safely."},
        ]


def get_default_questions_for_skill(skill_name: str, skill_slug: str) -> List[Dict[str, Any]]:

    """
    Returns 2 targeted multiple choice questions with correct answer stored server-side.
    """
    sn = skill_name.lower()

    if "html" in sn or "css" in sn:
        return [
            {
                "question": "Which HTML element is recommended for main navigation links?",
                "options": ["<nav>", "<div>", "<section>", "<header>"],
                "correct_index": 0,
                "explanation": "The semantic <nav> tag specifies a section intended for navigation links."
            },
            {
                "question": "In CSS Flexbox, which property aligns items along the main axis?",
                "options": ["align-items", "justify-content", "place-content", "flex-direction"],
                "correct_index": 1,
                "explanation": "justify-content defines the alignment along the main axis in Flexbox."
            }
        ]
    elif "javascript" in sn or "js" in sn or "es6" in sn:
        return [
            {
                "question": "What is the return type of `typeof NaN` in JavaScript?",
                "options": ["\"number\"", "\"nan\"", "\"undefined\"", "\"object\""],
                "correct_index": 0,
                "explanation": "NaN stands for Not-a-Number, but its Javascript primitive type is typeof 'number'."
            },
            {
                "question": "Which array method creates a new array populated with the results of calling a provided function?",
                "options": ["forEach()", "map()", "filter()", "reduce()"],
                "correct_index": 1,
                "explanation": "map() creates a new array populated with the results of calling a provided function on every element."
            }
        ]
    elif "react" in sn:
        return [
            {
                "question": "Which hook is used to handle side-effects in React functional components?",
                "options": ["useState", "useEffect", "useMemo", "useCallback"],
                "correct_index": 1,
                "explanation": "useEffect lets you synchronize a component with an external system or side-effect."
            },
            {
                "question": "What is the primary purpose of keys when rendering a list of elements in React?",
                "options": ["To style list items", "To help React identify which items have changed, added, or removed", "To count array items", "To trigger global state updates"],
                "correct_index": 1,
                "explanation": "Keys give elements a stable identity across renders to optimize DOM diffing."
            }
        ]
    elif "python" in sn:
        return [
            {
                "question": "Which of the following built-in Python data structures is mutable?",
                "options": ["Tuple", "List", "String", "Frozenset"],
                "correct_index": 1,
                "explanation": "Lists in Python are mutable, meaning their contents can be modified in place."
            },
            {
                "question": "What does the `pass` statement do in Python?",
                "options": ["Terminates the function", "Acts as a null syntax placeholder", "Skips to the next iteration", "Raises a SyntaxError"],
                "correct_index": 1,
                "explanation": "pass is a null operation; nothing happens when it executes."
            }
        ]
    elif "math" in sn or "stats" in sn or "linear" in sn:
        return [
            {
                "question": "What is the result of multiplying a 3x2 matrix by a 2x4 matrix?",
                "options": ["3x4 matrix", "2x2 matrix", "3x2 matrix", "Cannot be multiplied"],
                "correct_index": 0,
                "explanation": "The inner dimensions match (2=2), resulting in a matrix of dimensions 3x4."
            },
            {
                "question": "Which metric measures the spread of data relative to its mean?",
                "options": ["Median", "Standard Deviation", "Mode", "Quantile"],
                "correct_index": 1,
                "explanation": "Standard deviation measures the amount of variation or dispersion of a set of values."
            }
        ]
    elif "data" in sn or "pandas" in sn or "numpy" in sn:
        return [
            {
                "question": "In Pandas, which method is used to remove missing values from a DataFrame?",
                "options": ["fillna()", "dropna()", "isna()", "drop_duplicates()"],
                "correct_index": 1,
                "explanation": "dropna() removes rows or columns containing missing values."
            },
            {
                "question": "What is the main advantage of NumPy arrays over standard Python lists?",
                "options": ["Dynamic typing", "Vectorized contiguous memory operations", "Automatic database syncing", "Thread safety"],
                "correct_index": 1,
                "explanation": "NumPy arrays use contiguous C-memory blocks for vectorized numerical speed."
            }
        ]
    else:
        return [
            {
                "question": f"What is a core prerequisite concept in {skill_name}?",
                "options": ["Syntax & Fundamentals", "Advanced Optimization", "Database Indexing", "Container Deployment"],
                "correct_index": 0,
                "explanation": f"Understanding syntax and core primitives is essential for mastering {skill_name}."
            },
            {
                "question": f"Which best practice applies when applying {skill_name} in production?",
                "options": ["Hardcode credentials", "Modular structured clean code", "Ignore exception handling", "Disable logging"],
                "correct_index": 1,
                "explanation": "Modular code with robust error handling ensures production reliability."
            }
        ]


def generate_and_save_diagnostic_questions(db: Session, goal_id: int) -> List[DiagnosticQuestion]:
    """
    Generates approx 2 questions per skill for the goal and saves to DB (including correct_index).
    """
    from db.database import lock_goal_write
    lock_goal_write(db, goal_id)
    existing = db.query(DiagnosticQuestion).filter(
        DiagnosticQuestion.goal_id == goal_id,
        ~DiagnosticQuestion.skill_slug.startswith("verif_")
    ).all()
    if existing:
        return existing

    skills = db.query(Skill).filter(Skill.goal_id == goal_id).all()
    if not skills:
        return []

    created_questions = []
    total_q_count = 0
    max_questions = 10  # Cap total questions for lightweight diagnostic

    for s in skills:
        if total_q_count >= max_questions:
            break

        skill_slug = f"skill_{s.id}"
        q_templates = get_default_questions_for_skill(s.name, skill_slug)

        for q_data in q_templates:
            if total_q_count >= max_questions:
                break

            q_row = DiagnosticQuestion(
                goal_id=goal_id,
                skill_db_id=s.id,
                skill_slug=skill_slug,
                skill_name=s.name,
                question=q_data["question"],
                options=q_data["options"],
                correct_index=q_data["correct_index"],
                explanation=q_data["explanation"]
            )
            db.add(q_row)
            db.flush()
            created_questions.append(q_row)
            total_q_count += 1

    db.commit()
    return created_questions


def grade_diagnostic_submission(
    db: Session,
    goal_id: int,
    user_answers: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Grades user submitted answers against server-side correct_index, updates Mastery table, and returns report.
    """
    questions = db.query(DiagnosticQuestion).filter(
        DiagnosticQuestion.goal_id == goal_id,
        ~DiagnosticQuestion.skill_slug.startswith("verif_")
    ).all()
    q_map = {q.id: q for q in questions}

    answer_map = {a["question_id"]: a["selected_option"] for a in user_answers}

    from fastapi import HTTPException
    if not questions or len(answer_map) != len(user_answers) or set(answer_map) != set(q_map):
        raise HTTPException(422, "Answer every diagnostic question exactly once. Reload the diagnostic if needed.")

    # Group scores by skill
    skill_stats = {}  # skill_db_id -> { total: int, correct: int, name: str, slug: str }

    for q in questions:
        if q.skill_db_id not in skill_stats:
            skill_stats[q.skill_db_id] = {
                "total": 0,
                "correct": 0,
                "name": q.skill_name,
                "slug": q.skill_slug
            }

        skill_stats[q.skill_db_id]["total"] += 1
        user_sel = answer_map.get(q.id)

        if user_sel is not None and user_sel == q.correct_index:
            skill_stats[q.skill_db_id]["correct"] += 1

    # Calculate mastery percentage per skill and persist in Masteries table
    mastery_report = []

    for skill_db_id, stats in skill_stats.items():
        total = stats["total"]
        correct = stats["correct"]
        score_pct = int(round((correct / total) * 100)) if total > 0 else 0

        # Upsert Mastery in DB
        mastery_row = (
            db.query(Mastery)
            .filter(Mastery.goal_id == goal_id, Mastery.skill_id == skill_db_id)
            .first()
        )
        if not mastery_row:
            mastery_row = Mastery(
                goal_id=goal_id,
                skill_id=skill_db_id,
                diagnostic_score=score_pct / 100.0,
                verified=False
            )
            db.add(mastery_row)
        else:
            mastery_row.diagnostic_score = score_pct / 100.0

        mastery_report.append({
            "skill_id": stats["slug"],
            "skill_db_id": skill_db_id,
            "skill_name": stats["name"],
            "score": score_pct
        })

    db.commit()

    return {
        "goal_id": goal_id,
        "mastery": mastery_report
    }
