from django.utils import timezone
from .models import ComplaintPoll

def evaluate_active_polls():
    now = timezone.now()
    expired_polls = ComplaintPoll.objects.filter(poll_status='active', closes_at__lte=now)
    
    for poll in expired_polls:
        total_votes = poll.vote_yes_count + poll.vote_no_count
        poll.poll_status = 'closed'
        
        if total_votes == 0:
            poll.priority_flag = 'none'
            print(f"NOTIFY ADMIN: Poll '{poll.complaint_title}' closed silently with 0 votes.")
            print(f"NOTIFY TENANT ({poll.raised_by.username}): Your poll '{poll.complaint_title}' received no votes and has been closed.")
        else:
            yes_ratio = poll.vote_yes_count / total_votes
            if yes_ratio >= 0.60:
                poll.priority_flag = 'high'
                print(f"NOTIFY ADMIN (HIGH PRIORITY): Complaint poll '{poll.complaint_title}' reached majority threshold ({yes_ratio*100:.1f}% yes). Requires attention.")
            elif yes_ratio >= 0.40:
                poll.priority_flag = 'medium'
            else:
                poll.priority_flag = 'low'
            print(f"NOTIFY TENANT ({poll.raised_by.username}): Your poll '{poll.complaint_title}' closed. Results: Yes={poll.vote_yes_count}, No={poll.vote_no_count}.")
            
        poll.save()
