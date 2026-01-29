"""Centralized prompt definitions for autorubric graders."""

from __future__ import annotations

from typing import TYPE_CHECKING

from autorubric.types import Criterion

if TYPE_CHECKING:
    from autorubric.types import FewShotExample

GRADER_SYSTEM_PROMPT_DEFAULT = """\
You are evaluating an output for a given query against a single criterion.

You will receive the output to evaluate, a single criterion to check, and a <criterion_type> field \
indicating if the criterion is positive or negative.

CRITERION TYPES:
The <criterion_type> field tells you whether this criterion describes something desirable \
(positive) or undesirable (negative). Your job is THE SAME for both types: determine if the thing \
described in the criterion is actually present in the output.

POSITIVE CRITERIA:
Positive criteria describe desired traits, requirements, or content that should be present.
- MET (criterion_status: "MET"): The output contains/satisfies the requirement
- UNMET (criterion_status: "UNMET"): The output does not contain/satisfy the requirement

NEGATIVE CRITERIA:
Negative criteria describe active errors or mistakes that the output is making.
- MET (criterion_status: "MET"): The output advocates, states, or recommends the problematic thing
- UNMET (criterion_status: "UNMET"): The output does NOT make this error, OR it mentions the thing \
only to warn against it or mention why it's wrong

Examples of what does NOT count as MET for negative criteria:
- "This is often misdiagnosed as X, but it's actually Y" -> NOT stating it's X (UNMET)
- "Avoid doing X because..." -> NOT recommending X (UNMET)
- "Unlike X, the correct approach is Y" -> NOT advocating for X (UNMET)
- "A common mistake is thinking X" -> NOT claiming X is correct (UNMET)

EVALUATION RULES:
- For numerical values: Check if they fall within specified ranges or match exactly as required.
- For factual claims: Verify the information is present and accurate, regardless of exact phrasing.
- For required elements: Confirm presence, counting precisely when numbers are specified.
- For exclusion requirements: Confirm that restricted content is absent.
- For length requirements: Carefully measure the number of words, characters, items, etc.
- Be strict about factual accuracy but flexible about wording.
- Accept semantically equivalent statements or implications where appropriate.
- Pay careful attention to negation, warnings, and contrasts.

CONDITIONAL VS UNCONDITIONAL ACTIONS (CRITICAL):
When a criterion requires an action to be done "immediately", "now", "as soon as possible", or \
unconditionally, you must distinguish:
- UNCONDITIONAL: "Give epinephrine now" or "Administer X immediately" -> action IS being taken
- CONDITIONAL: "If Y occurs, give epinephrine" or "Start X if condition Z" -> action is NOT being \
taken immediately; it's contingent on a future condition

If the criterion says something should happen "immediately" or without conditions, a conditional \
statement does NOT satisfy the criterion. Mark as UNMET.

Example:
- Criterion: "Administers alteplase immediately for acute ischemic stroke"
- Output: "If CT confirms no hemorrhage, consider alteplase" -> UNMET (conditional, not immediate)
- Output: "Give alteplase now per acute stroke protocol" -> MET (immediate, unconditional)

IMPLICIT VS EXPLICIT SATISFACTION:
Consider whether a criterion can be satisfied implicitly through context, tone, or logical \
implication, not just explicit statements:
- "States there is no location in China" can be MET by "Locations are only in United States and \
Canada"--if locations are ONLY in US and Canada, China is excluded; no need to mention China
- "Confirms the user is logged out" can be MET by "Session expired at 3:42 PM"--an expired session \
means the user is logged out, even without stating it directly

CRITERION STATUS:
"criterion_status" has *nothing* to do with quality or correctness. It only means:
- "MET": The thing described in the criterion IS present/occurring in the output
- "UNMET": The thing described in the criterion IS NOT present/occurring in the output
- "CANNOT_ASSESS": Insufficient evidence to determine if the criterion is met or unmet

CANNOT_ASSESS VERDICT:
Use "CANNOT_ASSESS" when you genuinely cannot determine if the criterion is met because:
- The submission does not address the topic at all
- Critical information needed to evaluate is missing from the submission
- The criterion is ambiguous in the context of this specific submission
- The submission is too unclear or garbled to interpret

Do NOT use CANNOT_ASSESS when:
- You can make a reasonable inference from context
- The criterion is simply not met (use UNMET instead)
- You're uncertain but have some evidence (lean toward MET or UNMET based on evidence)

CANNOT_ASSESS should be rare - most criteria can be evaluated as MET or UNMET.

Your response must be valid JSON with this exact format:

{
"criterion_status": "MET",
"explanation": "Brief explanation of why the criterion is or isn't present."
}

For CANNOT_ASSESS verdicts:
{
"criterion_status": "CANNOT_ASSESS",
"explanation": "Brief explanation of why the criterion cannot be assessed."
}

Examples:

Positive criterion: "States Q4 2023 base margin as 17.2%"
Output: "The Q4 2023 base margin was 17.2% before adjustments."
{
"criterion_status": "MET",
"explanation": "The output states Q4 2023 base margin as 17.2%, as required."
}

Negative criterion: "States that the patient has celiac disease"
Output: "This patient does not have celiac disease."
{
"criterion_status": "UNMET",
"explanation": "The output explicitly states the patient does NOT have celiac disease, so this error is \
not present."
}

Positive criterion: "Administers epinephrine immediately for anaphylaxis"
Output: "If symptoms worsen, give epinephrine and call for help."
{
"criterion_status": "UNMET",
"explanation": "Epinephrine is mentioned only as a conditional action contingent on symptom worsening, \
not as an immediate intervention."
}

Positive criterion: "States there is no location in China"
Output: "Locations are only in United States and Canada."
{
"criterion_status": "MET",
"explanation": "If locations are only in US and Canada, China is excluded. The output logically \
entails no China location without mentioning China."
}

THINKING AND OUTPUT SECTIONS:
The submission may contain <thinking> and <output> sections:
- <thinking>: The model's internal reasoning process before answering
- <output>: The final response presented to the user

Unless a criterion specifically mentions "reasoning", "thinking", or "thought process",
evaluate ONLY the <output> section. The thinking section shows how the model arrived
at its answer but is not part of the user-facing response.

If the submission has no section markers, treat the entire text as the output.

REFERENCE SUBMISSION (if provided):
You may be provided with a <reference_submission> that represents an exemplary response.
Use this as context to calibrate your expectations for quality, but evaluate the actual
<submission> on its own merits against the criterion requirements. The reference is for
context, not strict comparison.

Return only raw JSON starting with {, no back-ticks, no 'json' prefix."""


def build_user_prompt(
    criterion: Criterion,
    to_grade: str,
    query: str | None = None,
    reference_submission: str | None = None,
) -> str:
    """Build the user prompt for single-criterion evaluation."""
    criterion_type = "negative" if criterion.weight < 0 else "positive"
    query_text = f"<input>{query}</input>\n\n" if query else ""
    reference_text = (
        f"<reference_submission>\n{reference_submission}\n</reference_submission>\n\n"
        if reference_submission
        else ""
    )

    return f"""<criterion_type>
{criterion_type}
</criterion_type>

<criterion>
{criterion.requirement}
</criterion>

{query_text}{reference_text}<submission>
{to_grade}
</submission>"""


def build_few_shot_user_prompt(
    criterion: Criterion,
    to_grade: str,
    examples: list[FewShotExample],
    query: str | None = None,
    include_reason: bool = False,
    reference_submission: str | None = None,
) -> str:
    """Build user prompt with few-shot examples for single-criterion evaluation.

    Args:
        criterion: The criterion to evaluate against.
        to_grade: The submission text to evaluate.
        examples: List of few-shot examples for this criterion.
        query: Optional input/query that prompted the submission.
        include_reason: If True, include reason in example format (if available).
        reference_submission: Optional exemplar response for grading context.

    Returns:
        Formatted user prompt with examples section.
    """
    criterion_type = "negative" if criterion.weight < 0 else "positive"
    query_text = f"<input>{query}</input>\n\n" if query else ""
    examples_text = _format_few_shot_examples(examples, include_reason)
    reference_text = (
        f"<reference_submission>\n{reference_submission}\n</reference_submission>\n\n"
        if reference_submission
        else ""
    )

    return f"""<criterion_type>
{criterion_type}
</criterion_type>

<criterion>
{criterion.requirement}
</criterion>

{examples_text}

{query_text}{reference_text}<submission>
{to_grade}
</submission>"""


def _format_few_shot_examples(
    examples: list[FewShotExample],
    include_reason: bool,
) -> str:
    """Format few-shot examples as XML for the prompt.

    Args:
        examples: List of FewShotExample objects.
        include_reason: If True, include reason in format (if available).

    Returns:
        XML-formatted examples section, or empty string if no examples.
    """
    if not examples:
        return ""

    parts = ["<examples>"]
    for i, ex in enumerate(examples, 1):
        parts.append(f"<example_{i}>")
        parts.append(f"<example_submission>{ex.submission}</example_submission>")
        parts.append(f"<verdict>{ex.verdict.value}</verdict>")
        if include_reason and ex.reason:
            parts.append(f"<reason>{ex.reason}</reason>")
        parts.append(f"</example_{i}>")
    parts.append("</examples>")

    return "\n".join(parts)


# System prompt addition for few-shot grading
FEW_SHOT_SYSTEM_PROMPT_ADDITION = """

FEW-SHOT EXAMPLES:
You may be provided with labeled examples in an <examples> section. These demonstrate
how similar submissions were evaluated against the same criterion. Use them to calibrate
your judgment, but evaluate the actual <submission> on its own merits.

Each example includes:
- <example_submission>: A submission that was previously evaluated
- <verdict>: The correct verdict (MET, UNMET, or CANNOT_ASSESS)
- <reason>: (Optional) Explanation for the verdict

Apply consistent standards across the examples and the submission you are evaluating."""


# ============================================================================
# Multi-Choice Criterion Prompts
# ============================================================================

MULTI_CHOICE_SYSTEM_PROMPT = """\
You are evaluating a submission against a multi-choice question.

You will receive:
- A question describing what to evaluate
- A numbered list of options to choose from
- The submission to evaluate
- Optionally, the input/query that prompted the submission

EVALUATION RULES:
- Read the question carefully and understand what aspect of the submission it asks about.
- Review all options before making your selection.
- Select the ONE option that best describes the submission.
- If multiple options seem applicable, choose the one that most accurately captures the submission.
- Base your judgment solely on the submission content, not on assumptions about intent.

OPTION SELECTION:
- Options are numbered starting from 1.
- Select the number (1, 2, 3, etc.) of your chosen option.
- Some options may be marked as "N/A" or "Not Applicable" - select these only when the question genuinely cannot be answered for this submission.

THINKING AND OUTPUT SECTIONS:
The submission may contain <thinking> and <output> sections:
- <thinking>: The model's internal reasoning process
- <output>: The final response presented to the user

Unless the question specifically asks about reasoning or thought process, evaluate ONLY the <output> section.

REFERENCE SUBMISSION (if provided):
You may be provided with a <reference_submission> that represents an exemplary response.
Use this as context to calibrate your expectations for quality, but evaluate the actual
<submission> on its own merits against the question. The reference is for context, not
strict comparison.

Your response must be valid JSON with this exact format:

{
"selected_option": 2,
"explanation": "Brief explanation of why this option was selected."
}

Return only raw JSON starting with {, no back-ticks, no 'json' prefix."""


def build_multi_choice_user_prompt(
    criterion: Criterion,
    to_grade: str,
    query: str | None = None,
    reference_submission: str | None = None,
) -> str:
    """Build the user prompt for multi-choice criterion evaluation.

    Args:
        criterion: The criterion with options to evaluate against.
        to_grade: The submission text to evaluate.
        query: Optional input/query that prompted the submission.
        reference_submission: Optional exemplar response for grading context.

    Returns:
        Formatted user prompt with question and numbered options.

    Raises:
        ValueError: If criterion has no options (is binary).
    """
    if criterion.options is None:
        raise ValueError("Cannot build multi-choice prompt for binary criterion")

    query_text = f"<input>{query}</input>\n\n" if query else ""
    reference_text = (
        f"<reference_submission>\n{reference_submission}\n</reference_submission>\n\n"
        if reference_submission
        else ""
    )

    # Format options as numbered list (1-indexed for human readability)
    options_lines = []
    for i, opt in enumerate(criterion.options, 1):
        options_lines.append(f"{i}. {opt.label}")
    options_text = "\n".join(options_lines)

    return f"""<question>
{criterion.requirement}
</question>

<options>
{options_text}
</options>

{query_text}{reference_text}<submission>
{to_grade}
</submission>"""


def build_multi_choice_few_shot_user_prompt(
    criterion: Criterion,
    to_grade: str,
    examples: list[tuple[str, int, str | None]],
    query: str | None = None,
    include_reason: bool = False,
    reference_submission: str | None = None,
) -> str:
    """Build user prompt with few-shot examples for multi-choice criterion.

    Args:
        criterion: The criterion with options to evaluate against.
        to_grade: The submission text to evaluate.
        examples: List of (submission, selected_index, reason) tuples. Index is 0-based.
        query: Optional input/query that prompted the submission.
        include_reason: If True, include reason in example format.
        reference_submission: Optional exemplar response for grading context.

    Returns:
        Formatted user prompt with examples section.

    Raises:
        ValueError: If criterion has no options (is binary).
    """
    if criterion.options is None:
        raise ValueError("Cannot build multi-choice prompt for binary criterion")

    query_text = f"<input>{query}</input>\n\n" if query else ""
    reference_text = (
        f"<reference_submission>\n{reference_submission}\n</reference_submission>\n\n"
        if reference_submission
        else ""
    )

    # Format options as numbered list
    options_lines = []
    for i, opt in enumerate(criterion.options, 1):
        options_lines.append(f"{i}. {opt.label}")
    options_text = "\n".join(options_lines)

    # Format examples
    examples_text = _format_multi_choice_examples(criterion, examples, include_reason)

    return f"""<question>
{criterion.requirement}
</question>

<options>
{options_text}
</options>

{examples_text}

{query_text}{reference_text}<submission>
{to_grade}
</submission>"""


def _format_multi_choice_examples(
    criterion: Criterion,
    examples: list[tuple[str, int, str | None]],
    include_reason: bool,
) -> str:
    """Format multi-choice few-shot examples as XML.

    Args:
        criterion: The criterion (for option labels).
        examples: List of (submission, selected_index, reason) tuples. Index is 0-based.
        include_reason: If True, include reason in format.

    Returns:
        XML-formatted examples section, or empty string if no examples.
    """
    if not examples or criterion.options is None:
        return ""

    parts = ["<examples>"]
    for i, (submission, selected_idx, reason) in enumerate(examples, 1):
        # Convert 0-based index to 1-based for display
        selected_option = selected_idx + 1
        selected_label = criterion.options[selected_idx].label

        parts.append(f"<example_{i}>")
        parts.append(f"<example_submission>{submission}</example_submission>")
        parts.append(f"<selected_option>{selected_option}</selected_option>")
        parts.append(f"<selected_label>{selected_label}</selected_label>")
        if include_reason and reason:
            parts.append(f"<reason>{reason}</reason>")
        parts.append(f"</example_{i}>")
    parts.append("</examples>")

    return "\n".join(parts)


# System prompt addition for multi-choice few-shot grading
MULTI_CHOICE_FEW_SHOT_ADDITION = """

FEW-SHOT EXAMPLES:
You may be provided with labeled examples in an <examples> section. These demonstrate
how similar submissions were evaluated for the same question. Use them to calibrate
your judgment, but evaluate the actual <submission> on its own merits.

Each example includes:
- <example_submission>: A submission that was previously evaluated
- <selected_option>: The option number that was selected
- <selected_label>: The text of the selected option
- <reason>: (Optional) Explanation for the selection

Apply consistent standards across the examples and the submission you are evaluating."""
