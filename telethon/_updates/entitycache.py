from .session import EntityType, Entity


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
            self.hash_map[id] = Entity(EntityType.BOT if bot else EntityType.USER, id, hash)

    def get(self, id):
        return self.hash_map.get(id)

    def extend(self, users, chats):
        # See https://core.telegram.org/api/min for "issues" with "min constructors".
        self.hash_map.update(
            (u.id, Entity(EntityType.BOT if u.bot else EntityType.USER, u.id, u.access_hash))
            for u in users
            if getattr(u, 'access_hash', None) and not u.min
        )
        self.hash_map.update(
            (c.id, Entity(
                    (
                        EntityType.MEGAGROUP
                        if c.megagroup
                        else (EntityType.GIGAGROUP if getattr(c, "gigagroup", None) else EntityType.CHANNEL)
                    ),
                    c.id,
                    c.access_hash,
            ))
            for c in chats
            if getattr(c, 'access_hash', None) and not getattr(c, 'min', None)
        )

    def put(self, entity):
        self.hash_map[entity.id] = entity

    def retain(self, filter):
        self.hash_map = {k: v for k, v in self.hash_map.items() if filter(k)}

    def __len__(self):
        return len(self.hash_map)
