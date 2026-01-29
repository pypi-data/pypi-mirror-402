"""
CDC Stream - Django Signals
Handles automatic queue management when rules are created/deleted/updated.
Each alert gets its own queue and worker thread.
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from .models import Rule


@receiver(post_save, sender=Rule)
def rule_post_save(sender, instance, created, **kwargs):
    """Handle queue creation/update when rule is created or modified."""
    try:
        from cdc_stream.worker import on_rule_created, on_rule_updated

        if created:
            # New rule - create queue and worker
            if instance.is_active and instance.table_name:
                on_rule_created(instance)
        else:
            # Updated rule - update queue configuration
            on_rule_updated(instance)

    except ImportError:
        # Worker module not available (e.g., during migrations)
        pass
    except Exception as e:
        # Don't let signal errors break the save
        print(f"Signal error (post_save): {e}")


@receiver(pre_delete, sender=Rule)
def rule_pre_delete(sender, instance, **kwargs):
    """Handle queue deletion when rule is deleted."""
    try:
        from cdc_stream.worker import on_rule_deleted

        # Delete queue and stop worker thread
        on_rule_deleted(instance.id)

    except ImportError:
        # Worker module not available
        pass
    except Exception as e:
        # Don't let signal errors break the delete
        print(f"Signal error (pre_delete): {e}")
