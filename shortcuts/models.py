from django.db import models

class Application(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    icon_svg = models.TextField(help_text="Inline SVG path code for premium graphic rendering")

    def __str__(self):
        return self.name

class Shortcut(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    CATEGORY_CHOICES = [
        ('navigation', 'Navigation'),
        ('editing', 'Editing'),
        ('window', 'Window Management'),
        ('terminal', 'Terminal / CLI'),
        ('system', 'System Actions'),
        ('formatting', 'Formatting'),
        ('search', 'Search & Replace'),
        ('other', 'Miscellaneous'),
    ]

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='shortcuts')
    keys_windows = models.CharField(max_length=100, help_text="e.g., Ctrl+Shift+P")
    keys_mac = models.CharField(max_length=100, help_text="e.g., Cmd+Shift+P")
    description = models.CharField(max_length=255)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy')
    estimated_time_saved = models.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        default=2.0, 
        help_text="Estimated seconds saved per execution"
    )
    example = models.TextField(blank=True, default='', help_text="Contextual example of when to use it")

    def __str__(self):
        return f"{self.application.name}: {self.keys_windows} - {self.description}"
