from .session import Entity, EntityType
from .. import types, utils

_sentinel = object()


class EntityCache:
    def __init__(
        self,
        hash_map: dict = _sentinel,
        self_id: int = None,
        self_bot: bool = None
    ):
        self.hash_map = {} if hash_map is _sentinel else hash_map
        self.self_id = self_id
        self.self_bot = self_bot

    def set_self_user(self, id, bot, hash):
        self.self_id = id
        self.self_bot = bot
        if hash:
            self.hash_map[id] = (hash, EntityType.BOT if bot else EntityType.USER)

    def get(self, id):
        try:
            hash, ty = self.hash_map[id]
            return Entity(ty, id, hash)
        except KeyError:
            return None

    def extend(self, tlo):
        # See https://core.telegram.org/api/min for "issues" with "min constructors".
        if not isinstance(tlo, types.TLObject) and utils.is_list_like(tlo):
            # This may be a list of users already for instance
            entities = tlo
        else:
            entities = []
            if hasattr(tlo, 'user'):
                entities.append(tlo.user)
            if hasattr(tlo, 'chat'):
                entities.append(tlo.chat)
            if hasattr(tlo, 'chats') and utils.is_list_like(tlo.chats):
                entities.extend(tlo.chats)
            if hasattr(tlo, 'users') and utils.is_list_like(tlo.users):
                entities.extend(tlo.users)

        updated_entities = []
        for e in entities:
            if getattr(e, 'access_hash', None) and not getattr(e, 'min', None):
                _, peer_type = utils.resolve_id(e.id)
                key = e.id
                if peer_type == types.PeerUser:
                    entity_type = EntityType.BOT if e.bot else EntityType.USER
                else:
                    entity_type = EntityType.MEGAGROUP if e.megagroup else (
                        EntityType.GIGAGROUP if getattr(e, 'gigagroup', None) else EntityType.CHANNEL
                    )
                value = (
                    e.access_hash,
                    entity_type,
                )
                if self.hash_map.get(key) != value:
                    self.hash_map[key] = value
                    updated_entities.append(e)
        return updated_entities

    def put(self, entity):
        self.hash_map[entity.id] = (entity.hash, entity.ty)

    def retain(self, filter):
        self.hash_map = {k: v for k, v in self.hash_map.items() if filter(k)}

    def __len__(self):
        return len(self.hash_map)
