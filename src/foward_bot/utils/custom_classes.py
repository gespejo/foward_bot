# coding=utf-8
from __future__ import unicode_literals

from telegram import Update
from telegram.ext import ConversationHandler
from telegram.utils.helpers import extract_chat_and_user
from telegram.utils.promise import Promise


class GoodConversationHandler(ConversationHandler):

    def check_update(self, update):

        if not isinstance(update, Update):
            return False

        chat, user = extract_chat_and_user(update)
        if not user:
            return False

        key = (chat.id, user.id) if chat else (None, user.id)
        state = self.conversations.get(key)

        # Resolve promises
        if isinstance(state, tuple) and len(state) is 2 and isinstance(state[1], Promise):
            self.logger.debug('waiting for promise...')

            old_state, new_state = state
            new_state.result(timeout=self.run_async_timeout)

            if new_state.done.is_set():
                self.update_state(new_state.result(), key)
                state = self.conversations.get(key)

            else:
                for candidate in (self.timed_out_behavior or []):
                    if candidate.check_update(update):
                        # Save the current user and the selected handler for handle_update
                        self.current_conversation = key
                        self.current_handler = candidate

                        return True

                else:
                    return False

        self.logger.debug('selecting conversation %s with state %s' % (str(key), str(state)))

        handler = None

        # Search entry points for a match
        if state is None or self.allow_reentry:
            for entry_point in self.entry_points:
                if entry_point.check_update(update):
                    handler = entry_point
                    break

            else:
                if state is None:
                    return False

        # Get the handler list for current state, if we didn't find one yet and we're still here
        if state is not None and not handler:
            handlers = self.states.get(state)

            for candidate in (handlers or []):
                if candidate.check_update(update):
                    handler = candidate
                    break

            # Find a fallback handler if all other handlers fail
            else:
                for fallback in self.fallbacks:
                    if fallback.check_update(update):
                        handler = fallback
                        break

                else:
                    return False

        # Save the current user and the selected handler for handle_update
        self.current_conversation = key
        self.current_handler = handler

        return True
