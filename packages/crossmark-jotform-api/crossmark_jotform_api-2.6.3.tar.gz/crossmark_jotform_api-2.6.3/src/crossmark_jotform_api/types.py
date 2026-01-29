from typing import Optional, Union, Dict, List, Any, TypedDict

try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired


AnswerType = Optional[Union[str, List[str], Dict[str, Any]]]


class AnswerValue(TypedDict):
    text: NotRequired[str]
    key: str
    order: NotRequired[str]
    answer: NotRequired[AnswerType]
    prettyFormat: NotRequired[str]
    file: NotRequired[Optional[str]]
    type: NotRequired[str]
    name: Optional[NotRequired[str]]


AnswersDict = Dict[str, AnswerValue]


class Submission(TypedDict):
    id: str
    form_id: str
    ip: str
    created_at: str
    updated_at: str
    status: str
    new: str
    answers: AnswersDict
    workflowStatus: NotRequired[str]
    limit_left: NotRequired[int]  # Only present in single submission response


class JotformApiSubmissionContent(Submission):
    submissionID: str


class JotformCreateSubmissionResponse(TypedDict):
    responseCode: int
    message: str
    content: Dict[str, JotformApiSubmissionContent]


class JotformAPIResponse(TypedDict):
    responseCode: int
    message: str
    content: List[JotformApiSubmissionContent]
    limit_left: int  # For list submissions endpoint


class JotformSingleSubmissionResponse(TypedDict):
    responseCode: int
    message: str
    content: JotformApiSubmissionContent


class FormObject(TypedDict, total=False):
    id: str
    username: str
    title: str
    height: str
    status: str
    created_at: str
    updated_at: str
    last_submission: str
    new: str
    count: str
    type: str
    favorite: str
    archived: str
    url: str


class JotformFormAPIResponse(TypedDict):
    responseCode: int
    message: str
    content: FormObject
    limit_left: int  # mapped from "limit-left" in JSON
