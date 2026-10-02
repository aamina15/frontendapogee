import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models.skill import Skill
from models.mastery import Mastery
from models.diagnostic import DiagnosticQuestion

logger = logging.getLogger("apogee.diagnostic_service")


def get_verification_questions_for_skill(skill_name: str, skill_slug: str = "") -> List[Dict[str, Any]]:
    """
    Returns five curated verification questions for supported skills; otherwise none.
    Correct answers (correct_index) are stored server-side only — never sent to frontend.
    """
    sn = skill_name.lower()
    if 'test' in sn and any(t in sn for t in ('react', 'frontend', 'jest', 'rtl')):
        sn = 'frontend testing'
    elif 'react' in sn and any(t in sn for t in ('redux', 'zustand', 'state management')):
        sn = 'state management redux'

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
        # Unknown skills remain unassessed; generic programming trivia is not proof.
        return []


def get_default_questions_for_skill(skill_name: str, skill_slug: str) -> List[Dict[str, Any]]:
    bank = get_verification_questions_for_skill(skill_name, skill_slug)
    return bank[2:4]


# Goal-aware diagnostic sizing: the quick assessment asks ONE question per
# skill (so the count reflects the graph) and the optional deeper assessment
# tops up to two per skill. Caps keep even large graphs lightweight.
QUICK_MAX_QUESTIONS = 10
DEEP_MAX_QUESTIONS = 12


def generate_and_save_diagnostic_questions(
    db: Session, goal_id: int, depth: str = "quick"
) -> List[DiagnosticQuestion]:
    """
    Generates goal-aware diagnostic questions and saves them (including correct_index).

    Distribution (deterministic, coverage-first):
      - quick (default): 1 question per skill, capped at QUICK_MAX_QUESTIONS.
        Skills with validated AI or curated questions are assessed within the cap.
      - deep: tops up existing questions to 2 per skill, capped at DEEP_MAX_QUESTIONS.
        Existing questions are preserved; only missing second questions are added.

    Skills beyond the cap keep zero questions — they stay honestly UNASSESSED
    (no fabricated scores are ever written for them).
    """
    from db.database import lock_goal_write
    lock_goal_write(db, goal_id)
    existing = db.query(DiagnosticQuestion).filter(
        DiagnosticQuestion.goal_id == goal_id,
        ~DiagnosticQuestion.skill_slug.startswith("verif_")
    ).order_by(DiagnosticQuestion.id).all()

    skills = db.query(Skill).filter(Skill.goal_id == goal_id).order_by(Skill.id).all()
    if not skills:
        return []

    if existing and depth != "deep":
        # Idempotent: a diagnostic for this goal already exists; return it unchanged.
        return existing

    from models.goal import Goal
    from services.question_service import questions_for_skills
    goal = db.get(Goal, goal_id)
    existing_counts = {s.id: sum(q.skill_db_id == s.id for q in existing) for s in skills}
    target = 2 if depth == 'deep' else 1
    cap = DEEP_MAX_QUESTIONS if depth == 'deep' else QUICK_MAX_QUESTIONS
    remaining = max(0, cap - len(existing))
    counts = {s.id: 0 for s in skills}
    for round_number in range(target):
        for skill in skills:
            if remaining and existing_counts[skill.id] + counts[skill.id] <= round_number:
                counts[skill.id] += 1
                remaining -= 1
    additions = questions_for_skills(goal, skills, counts, [q.question for q in existing], 'diagnostic')
    # Existing questions are immutable. The top-up loop indexes after them.
    templates_by_skill = {s.id: [None] * existing_counts[s.id] + additions[s.id] for s in skills}

    created_questions = []

    if existing:
        # Deep top-up: round-robin one missing question per skill (in skill id
        # order) until each skill has 2 or the cap is reached.
        per_skill_count = {s.id: 0 for s in skills}
        for q in existing:
            if q.skill_db_id in per_skill_count:
                per_skill_count[q.skill_db_id] += 1
        total = len(existing)
        changed = True
        while changed and total < DEEP_MAX_QUESTIONS:
            changed = False
            for s in skills:
                if total >= DEEP_MAX_QUESTIONS:
                    break
                used = per_skill_count[s.id]
                if used < 2 and used < len(templates_by_skill[s.id]):
                    q_data = templates_by_skill[s.id][used]
                    q_row = DiagnosticQuestion(
                        goal_id=goal_id,
                        skill_db_id=s.id,
                        skill_slug=f"skill_{s.id}",
                        skill_name=s.name,
                        question=q_data["question"],
                        options=q_data["options"],
                        correct_index=q_data["correct_index"],
                        explanation=q_data["explanation"]
                    )
                    db.add(q_row)
                    db.flush()
                    created_questions.append(q_row)
                    per_skill_count[s.id] += 1
                    total += 1
                    changed = True
        db.commit()
        return existing + created_questions

    # Fresh generation: round-robin across ALL skills first (coverage before depth).
    per_skill_target = 2 if depth == "deep" else 1
    cap = DEEP_MAX_QUESTIONS if depth == "deep" else QUICK_MAX_QUESTIONS
    per_skill_count = {s.id: 0 for s in skills}
    total = 0
    changed = True
    while changed and total < cap:
        changed = False
        for s in skills:
            if total >= cap:
                break
            used = per_skill_count[s.id]
            if used < per_skill_target and used < len(templates_by_skill[s.id]):
                q_data = templates_by_skill[s.id][used]
                q_row = DiagnosticQuestion(
                    goal_id=goal_id,
                    skill_db_id=s.id,
                    skill_slug=f"skill_{s.id}",
                    skill_name=s.name,
                    question=q_data["question"],
                    options=q_data["options"],
                    correct_index=q_data["correct_index"],
                    explanation=q_data["explanation"]
                )
                db.add(q_row)
                db.flush()
                created_questions.append(q_row)
                per_skill_count[s.id] += 1
                total += 1
                changed = True

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
            "score": score_pct,
            "assessed": True,
        })

    db.commit()

    return {
        "goal_id": goal_id,
        "mastery": mastery_report
    }
