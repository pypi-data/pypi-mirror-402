from enum import Enum


class Events(str, Enum):
    READY = "ready"
    MESSAGE_NEW = "message:new"
    MESSAGE_EDIT = "message:edit"
    MESSAGE_DELETE = "message:delete"
    MESSAGE_REACTION_ADD = "message:reaction_add"
    MESSAGE_REACTION_REMOVE = "message:reaction_remove"
    SERVER_MEMBER_JOIN = "server:member_join"
    SERVER_MEMBER_LEAVE = "server:member_leave"
    TYPING_START = "typing:start"
    PRESENCE_UPDATE = "presence:update"
    INTERACTION_BUTTON = "interaction:button"
    SESSION_EXPIRED = "session:expired"
    CONNECT = "connect"
