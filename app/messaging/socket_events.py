"""
socket_events.py — Flask-SocketIO real-time chat events.
Registered in app/__init__.py via register_socket_events(socketio).
"""
from flask import request
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from datetime import datetime


def register_socket_events(socketio):

    @socketio.on('connect')
    def on_connect():
        if current_user.is_authenticated:
            # Each user joins a personal room for direct notifications
            join_room(f'user_{current_user.id}')

    @socketio.on('disconnect')
    def on_disconnect():
        pass

    @socketio.on('join_conversation')
    def on_join(data):
        """Client joins a conversation room."""
        if not current_user.is_authenticated:
            return
        from app.models import Conversation
        conv_id = data.get('conv_id')
        conv    = Conversation.query.get(conv_id)
        if not conv:
            return
        if conv.user1_id != current_user.id and conv.user2_id != current_user.id:
            return
        room = f'conv_{conv_id}'
        join_room(room)
        emit('status', {'msg': 'Joined conversation.'}, room=request.sid)

    @socketio.on('leave_conversation')
    def on_leave(data):
        conv_id = data.get('conv_id')
        leave_room(f'conv_{conv_id}')

    @socketio.on('send_message')
    def on_send_message(data):
        """Receive message from client, save to DB, broadcast to room."""
        if not current_user.is_authenticated:
            return
        from app import db
        from app.models import Conversation, Message, User
        from app.utils import create_notification

        conv_id = data.get('conv_id')
        body    = (data.get('body') or '').strip()
        if not body or len(body) > 1000:
            return

        conv = Conversation.query.get(conv_id)
        if not conv:
            return
        if conv.user1_id != current_user.id and conv.user2_id != current_user.id:
            return

        # Check messaging permission
        from sqlalchemy import or_, and_
        from app.models import Interest
        other_id = conv.user2_id if conv.user1_id == current_user.id else conv.user1_id
        plan     = current_user.active_subscription
        can_msg  = plan and plan.plan.can_message if plan else False
        if not can_msg:
            interest = Interest.query.filter(
                or_(
                    and_(Interest.sender_id   == current_user.id,
                         Interest.receiver_id == other_id),
                    and_(Interest.sender_id   == other_id,
                         Interest.receiver_id == current_user.id),
                ),
                Interest.status == 'accepted'
            ).first()
            can_msg = bool(interest)
        if not can_msg:
            emit('error', {'msg': 'Upgrade plan to send messages.'}, room=request.sid)
            return

        # Save message
        msg              = Message(conversation_id=conv_id,
                                   sender_id=current_user.id, body=body)
        conv.updated_at  = datetime.utcnow()
        db.session.add(msg)
        db.session.commit()

        payload = {
            'id':        msg.id,
            'body':      msg.body,
            'sender_id': msg.sender_id,
            'sent_at':   msg.sent_at.strftime('%I:%M %p'),
            'is_mine':   False,          # receiver sees is_mine=False
        }
        # Broadcast to room — each client sets is_mine based on sender_id
        emit('new_message', {**payload, 'sender_id': msg.sender_id},
             room=f'conv_{conv_id}')

        # In-app notification to receiver
        other = User.query.get(other_id)
        if other:
            create_notification(
                user_id    = other_id,
                notif_type = 'new_message',
                message    = f'{current_user.full_name} sent you a message.',
                link       = f'/messages/{conv_id}',
            )
            # Emit real-time notification badge update to receiver's personal room
            socketio.emit('notif_update', {}, room=f'user_{other_id}')

            # Email via Celery — never block the SocketIO event loop
            from app.tasks import send_message_email_task
            send_message_email_task.delay(other_id, current_user.full_name, body[:200], conv_id)

    # ── WebRTC Signalling (Phase 13.1) ───────────────────────────────────
    @socketio.on('webrtc_offer')
    def on_webrtc_offer(data):
        """Relay WebRTC offer from caller to callee."""
        if not current_user.is_authenticated:
            return
        conv_id  = data.get('conv_id')
        offer    = data.get('offer')
        call_type = data.get('call_type', 'video')   # 'video' or 'audio'
        if not conv_id or not offer:
            return
        from app.models import Conversation
        conv = Conversation.query.get(conv_id)
        if not conv:
            return
        if conv.user1_id != current_user.id and conv.user2_id != current_user.id:
            return
        # Relay to the other user's personal room
        other_id = conv.user2_id if conv.user1_id == current_user.id else conv.user1_id
        socketio.emit('webrtc_incoming_call', {
            'conv_id':   conv_id,
            'offer':     offer,
            'call_type': call_type,
            'caller_id':   current_user.id,
            'caller_name': current_user.full_name,
        }, room=f'user_{other_id}')

    @socketio.on('webrtc_answer')
    def on_webrtc_answer(data):
        """Relay WebRTC answer from callee back to caller."""
        if not current_user.is_authenticated:
            return
        caller_id = data.get('caller_id')
        answer    = data.get('answer')
        if caller_id and answer:
            socketio.emit('webrtc_answer', {
                'answer':    answer,
                'callee_id': current_user.id,
            }, room=f'user_{caller_id}')

    @socketio.on('webrtc_ice_candidate')
    def on_webrtc_ice(data):
        """Relay ICE candidate between peers."""
        if not current_user.is_authenticated:
            return
        target_id = data.get('target_id')
        candidate = data.get('candidate')
        if target_id and candidate:
            socketio.emit('webrtc_ice_candidate', {
                'candidate': candidate,
                'from_id':   current_user.id,
            }, room=f'user_{target_id}')

    @socketio.on('webrtc_hang_up')
    def on_webrtc_hang_up(data):
        """Signal hang-up to the other participant."""
        if not current_user.is_authenticated:
            return
        target_id = data.get('target_id')
        if target_id:
            socketio.emit('webrtc_hang_up', {
                'from_id': current_user.id,
            }, room=f'user_{target_id}')

    @socketio.on('webrtc_call_rejected')
    def on_call_rejected(data):
        """Signal that callee rejected the call."""
        if not current_user.is_authenticated:
            return
        caller_id = data.get('caller_id')
        if caller_id:
            socketio.emit('webrtc_call_rejected', {
                'from_id': current_user.id,
            }, room=f'user_{caller_id}')

    @socketio.on('typing')
    def on_typing(data):
        """Broadcast typing indicator to conversation room."""
        if not current_user.is_authenticated:
            return
        conv_id = data.get('conv_id')
        emit('user_typing',
             {'user': current_user.first_name, 'sender_id': current_user.id},
             room=f'conv_{conv_id}', include_self=False)
