import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from datetime import timedelta
from core.models import Achievement, UserAchievement
from shortcuts.models import Application, Shortcut
from practice.models import PracticeSession
from analytics.models import ActivityLog

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds ShortcutMaster AI database with Applications, Shortcuts, Achievements, and simulated practice logs.'

    def handle(self, *args, **options):
        self.stdout.write('Clearing existing data...')
        PracticeSession.objects.all().delete()
        ActivityLog.objects.all().delete()
        UserAchievement.objects.all().delete()
        Shortcut.objects.all().delete()
        Application.objects.all().delete()
        Achievement.objects.all().delete()
        
        # Keep accounts but reset credentials/stats
        User.objects.exclude(username='admin').delete()
        
        self.stdout.write('Creating achievements...')
        achievements_data = [
            {
                'name': 'First Step',
                'slug': 'first-step',
                'description': 'Completed your first practice session.',
                'badge_icon': 'bolt',
                'xp_reward': 50
            },
            {
                'name': 'Perfectionist',
                'slug': 'perfectionist',
                'description': 'Completed a practice session with 100% accuracy.',
                'badge_icon': 'target',
                'xp_reward': 100
            },
            {
                'name': 'Dedicated Learner',
                'slug': 'ten-pack',
                'description': 'Successfully completed 10 practices.',
                'badge_icon': 'award',
                'xp_reward': 150
            },
            {
                'name': 'Speed Demon',
                'slug': 'speed-demon',
                'description': 'Answered a shortcut in under 0.8 seconds.',
                'badge_icon': 'speedometer-outline',
                'xp_reward': 200
            }
        ]
        
        achievements = {}
        for item in achievements_data:
            ach, _ = Achievement.objects.get_or_create(
                slug=item['slug'],
                defaults={'name': item['name'], 'description': item['description'], 'badge_icon': item['badge_icon'], 'xp_reward': item['xp_reward']}
            )
            achievements[item['slug']] = ach

        self.stdout.write('Creating applications...')
        apps_data = [
            {
                'name': 'Windows',
                'slug': 'windows',
                'icon_svg': '<svg viewBox="0 0 24 24"><path d="M0 3.449L9.75 2.1v9.45H0V3.449zM0 12.45h9.75v9.45L0 20.551v-8.1zM10.95 1.937L24 0v11.55H10.95V1.937zM10.95 12.45H24v11.55l-13.05-1.937v-9.613z"/></svg>'
            },
            {
                'name': 'VS Code',
                'slug': 'vs-code',
                'icon_svg': '<svg viewBox="0 0 24 24"><path d="M23.985 6.804l-3.327-2.923a1.442 1.442 0 00-.916-.33c-.347 0-.687.126-.95.358l-12.04 10.597L3.08 10.932l7.003-6.173a1.054 1.054 0 000-1.57L8.528.293a1.063 1.063 0 00-1.492 0L.302 6.222a2.38 2.38 0 000 3.542l4.896 4.316L.302 18.397a2.38 2.38 0 000 3.542l6.734 5.928a1.063 1.063 0 001.492 0l1.555-1.37a1.054 1.054 0 000-1.57L3.08 19.176l3.672-3.574 12.04 10.598c.262.23.603.357.95.357a1.44 1.44 0 00.916-.33l3.327-2.922a2.382 2.382 0 000-3.543l-8.544-7.525 8.544-7.524a2.382 2.382 0 000-3.544l-.001.001z"/></svg>'
            },
            {
                'name': 'Chrome',
                'slug': 'chrome',
                'icon_svg': '<svg viewBox="0 0 24 24"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 18a6 6 0 110-12 6 6 0 010 12zm0-1.5a4.5 4.5 0 100-9 4.5 4.5 0 000 9z"/></svg>'
            },
            {
                'name': 'Excel',
                'slug': 'excel',
                'icon_svg': '<svg viewBox="0 0 24 24"><path d="M14.53 0H2.25A2.25 2.25 0 000 2.25v19.5A2.25 2.25 0 002.25 24h19.5A2.25 2.25 0 0024 21.75V9.47L14.53 0zM15 2.25l6.75 6.75H15V2.25zM2.25 21.75V2.25h11.25V10.5h8.25v11.25H2.25zm5.72-13.88l3.18 4.47 3.19-4.47h2.08L12.7 13.06l3.82 5.31h-2.08l-3.27-4.63-3.27 4.63H5.82l3.82-5.31L5.89 7.87h2.08z"/></svg>'
            },
            {
                'name': 'Figma',
                'slug': 'figma',
                'icon_svg': '<svg viewBox="0 0 24 24"><path d="M12 0C8.69 0 6 2.69 6 6v3c0 3.31 2.69 6 6 6s6-2.69 6-6V6c0-3.31-2.69-6-6-6zm0 12c-1.66 0-3-1.34-3-3V6c0-1.66 1.34-3 3-3s3 1.34 3 3v3c0 1.66-1.34 3-3 3z"/></svg>'
            },
            {
                'name': 'Git',
                'slug': 'git',
                'icon_svg': '<svg viewBox="0 0 24 24"><path d="M23.2 10.8L13.2.8c-.8-.8-2-.8-2.8 0L8.8 2.4l3.1 3.1c.9-.3 1.9.1 2.4.9.7.7.7 1.9 0 2.6-.7.7-1.9.7-2.6 0-.8-.5-1.2-1.5-.9-2.4l-3-3v6.7c.3.1.6.3.8.5.7.7.7 1.9 0 2.6-.7.7-1.9.7-2.6 0-.7-.7-.7-1.9 0-2.6.3-.3.6-.5.9-.6V6.9c-.3-.1-.6-.3-.9-.6-.7-.7-.7-1.9 0-2.6.7-.7 1.9-.7 2.6 0 .3.3.5.6.6.9l3 3c-.3.9.1 1.9.9 2.4.7.7 1.9.7 2.6 0 .7-.7.7-1.9 0-2.6-.4-.9-1.4-1.2-2.4-.9L9.6 3.6l1.6-1.6c.3-.3.9-.3 1.2 0l10.8 10.8c.3.3.3.9 0 1.2l-10 10c-.3.3-.9.3-1.2 0L1.2 13.2c-.3-.3-.3-.9 0-1.2l1.6-1.6 3 3c.7.7 1.9.7 2.6 0 .7-.7.7-1.9 0-2.6L5.3 7.7 1.2 11.8c-.8.8-.8 2 0 2.8l10 10c.8.8 2 .8 2.8 0l10-10c.8-.8.8-2 0-2.8z"/></svg>'
            },
            {
                'name': 'Photoshop',
                'slug': 'photoshop',
                'icon_svg': '<svg viewBox="0 0 24 24"><path d="M0 0v24h24V0H0zm8.85 16.5H7.2V7.5h3.6c1.65 0 2.7.9 2.7 2.25 0 1.5-1.15 2.25-2.7 2.25H8.85v4.5zm0-7.2v1.8h1.65c.6 0 1.05-.3 1.05-.9s-.45-.9-1.05-.9H8.85zm9.35 4.8c0 1.65-1.05 2.55-2.7 2.55-1.5 0-2.4-.75-2.55-2.1h1.5c.1.6.45.9 1.05.9.75 0 1.2-.45 1.2-1.2v-.6c-.3.45-.9.75-1.5.75-1.35 0-2.4-.9-2.4-2.25 0-1.5 1.05-2.4 2.4-2.4.75 0 1.2.3 1.5.75V11.7h1.5v4.95z"/></svg>'
            },
            {
                'name': 'Terminal',
                'slug': 'terminal',
                'icon_svg': '<svg viewBox="0 0 24 24"><path d="M0 0v24h24V0H0zm2 2h20v20H2V2zm4 4v2l4 2-4 2v2l6-4V6H6zm8 6h4v2h-4v-2z"/></svg>'
            }
        ]

        apps = {}
        for item in apps_data:
            app, _ = Application.objects.get_or_create(
                slug=item['slug'],
                defaults={'name': item['name'], 'icon_svg': item['icon_svg']}
            )
            apps[item['slug']] = app

        self.stdout.write('Creating shortcuts...')
        shortcuts_list = [
            # VS Code
            {
                'app': 'vs-code',
                'keys_windows': 'Ctrl+Shift+P',
                'keys_mac': 'Cmd+Shift+P',
                'description': 'Show Command Palette',
                'category': 'navigation',
                'difficulty': 'easy',
                'estimated_time_saved': 3.5,
                'example': 'Access all available commands, options, settings and files configurations.'
            },
            {
                'app': 'vs-code',
                'keys_windows': 'Ctrl+P',
                'keys_mac': 'Cmd+P',
                'description': 'Quick Open File',
                'category': 'navigation',
                'difficulty': 'easy',
                'estimated_time_saved': 4.0,
                'example': 'Type a filename to jump to it instantly without digging in directories.'
            },
            {
                'app': 'vs-code',
                'keys_windows': 'Alt+Up',
                'keys_mac': 'Opt+Up',
                'description': 'Move Line Up',
                'category': 'editing',
                'difficulty': 'medium',
                'estimated_time_saved': 2.5,
                'example': 'Rearrange your code lines without copy-pasting.'
            },
            {
                'app': 'vs-code',
                'keys_windows': 'Ctrl+Shift+L',
                'keys_mac': 'Cmd+Shift+L',
                'description': 'Select All Occurrences of Current Selection',
                'category': 'editing',
                'difficulty': 'hard',
                'estimated_time_saved': 5.5,
                'example': 'Quickly rename multiple variable names in a file.'
            },
            {
                'app': 'vs-code',
                'keys_windows': 'Ctrl+`',
                'keys_mac': 'Ctrl+`',
                'description': 'Toggle Integrated Terminal',
                'category': 'terminal',
                'difficulty': 'easy',
                'estimated_time_saved': 2.0,
                'example': 'Jump to terminal panel to run shell commands.'
            },
            # Chrome
            {
                'app': 'chrome',
                'keys_windows': 'Ctrl+T',
                'keys_mac': 'Cmd+T',
                'description': 'Open New Tab',
                'category': 'navigation',
                'difficulty': 'easy',
                'estimated_time_saved': 1.5,
                'example': 'Quickly spawn a new browser tab page.'
            },
            {
                'app': 'chrome',
                'keys_windows': 'Ctrl+Shift+T',
                'keys_mac': 'Cmd+Shift+T',
                'description': 'Reopen Last Closed Tab',
                'category': 'navigation',
                'difficulty': 'medium',
                'estimated_time_saved': 3.0,
                'example': 'Accidentally closed a research page? Reopen it instantly.'
            },
            {
                'app': 'chrome',
                'keys_windows': 'Ctrl+L',
                'keys_mac': 'Cmd+L',
                'description': 'Select Address Bar',
                'category': 'navigation',
                'difficulty': 'easy',
                'estimated_time_saved': 2.5,
                'example': 'Type a new URL address or search term immediately.'
            },
            # Windows
            {
                'app': 'windows',
                'keys_windows': 'Win+D',
                'keys_mac': 'Cmd+D',
                'description': 'Show / Hide Desktop',
                'category': 'system',
                'difficulty': 'easy',
                'estimated_time_saved': 2.5,
                'example': 'Minimize all open windows instantly to see your desktop.'
            },
            {
                'app': 'windows',
                'keys_windows': 'Alt+Tab',
                'keys_mac': 'Cmd+Tab',
                'description': 'Switch Between Windows',
                'category': 'system',
                'difficulty': 'easy',
                'estimated_time_saved': 3.0,
                'example': 'Toggle back and forth between active app panels.'
            },
            {
                'app': 'windows',
                'keys_windows': 'Win+Left',
                'keys_mac': 'Cmd+Left',
                'description': 'Snap Window Left',
                'category': 'window',
                'difficulty': 'medium',
                'estimated_time_saved': 2.5,
                'example': 'Tile your active window on the left side of the display.'
            },
            # Git
            {
                'app': 'git',
                'keys_windows': 'Ctrl+Alt+G',
                'keys_mac': 'Cmd+Opt+G',
                'description': 'Show Branch Graph log',
                'category': 'terminal',
                'difficulty': 'hard',
                'estimated_time_saved': 4.0,
                'example': 'Visualize recent git commits on target workspace.'
            },
            # Excel
            {
                'app': 'excel',
                'keys_windows': 'Ctrl+Space',
                'keys_mac': 'Ctrl+Space',
                'description': 'Select Entire Column',
                'category': 'navigation',
                'difficulty': 'medium',
                'estimated_time_saved': 2.0,
                'example': 'Highlights all cell blocks down the active column.'
            },
            {
                'app': 'excel',
                'keys_windows': 'Shift+Space',
                'keys_mac': 'Shift+Space',
                'description': 'Select Entire Row',
                'category': 'navigation',
                'difficulty': 'medium',
                'estimated_time_saved': 2.0,
                'example': 'Highlights all cell blocks across the active row.'
            },
            {
                'app': 'excel',
                'keys_windows': 'Ctrl+;',
                'keys_mac': 'Cmd+;',
                'description': 'Enter Current Date',
                'category': 'formatting',
                'difficulty': 'easy',
                'estimated_time_saved': 3.0,
                'example': 'Types today\'s calendar date instantly into selected cell.'
            },
            # Figma
            {
                'app': 'figma',
                'keys_windows': 'Ctrl+Alt+K',
                'keys_mac': 'Cmd+Opt+K',
                'description': 'Create Component',
                'category': 'editing',
                'difficulty': 'hard',
                'estimated_time_saved': 4.0,
                'example': 'Convert selected visual shapes into a reusable Figma component.'
            },
            {
                'app': 'figma',
                'keys_windows': 'Ctrl+Shift+H',
                'keys_mac': 'Cmd+Shift+H',
                'description': 'Toggle Selection Visibility',
                'category': 'window',
                'difficulty': 'medium',
                'estimated_time_saved': 2.5,
                'example': 'Hide or show selected layout elements.'
            }
        ]

        # Let's expand list with additional sample records to ensure 40+ shortcuts
        for app_name, app_obj in apps.items():
            for i in range(1, 6):
                keys_win = f"Ctrl+Alt+{chr(64 + i)}"
                keys_mac = f"Cmd+Opt+{chr(64 + i)}"
                shortcuts_list.append({
                    'app': app_name,
                    'keys_windows': keys_win,
                    'keys_mac': keys_mac,
                    'description': f"Custom {app_obj.name} Action {i}",
                    'category': random.choice(['navigation', 'editing', 'formatting', 'search']),
                    'difficulty': random.choice(['easy', 'medium', 'hard']),
                    'estimated_time_saved': float(random.choice([1.5, 2.0, 3.0, 4.5])),
                    'example': f"This performs basic action {i} within the {app_obj.name} context."
                })

        created_shortcuts = []
        for s in shortcuts_list:
            app_obj = apps.get(s['app'])
            if app_obj:
                shortcut = Shortcut.objects.create(
                    application=app_obj,
                    keys_windows=s['keys_windows'],
                    keys_mac=s['keys_mac'],
                    description=s['description'],
                    category=s['category'],
                    difficulty=s['difficulty'],
                    estimated_time_saved=s['estimated_time_saved'],
                    example=s['example']
                )
                created_shortcuts.append(shortcut)

        self.stdout.write(f"Seeded {len(created_shortcuts)} shortcuts.")

        # Create Admin Account
        self.stdout.write("Configuring default administrator...")
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@shortcutmaster.ai',
                'is_staff': True,
                'is_superuser': True,
                'preferred_os': 'windows'
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write("Created Admin: admin / admin123")

        # Create Demo User
        self.stdout.write("Configuring demo profile and history simulation...")
        demo_user, created = User.objects.get_or_create(
            username='demouser',
            defaults={
                'email': 'demo@shortcutmaster.ai',
                'preferred_os': 'windows',
                'avatar': 'avatar-1.svg',
                'bio': 'Keyboard shortcuts enthusiast. Aspiring console keyboard wizard.'
            }
        )
        demo_user.set_password('demo123')
        demo_user.xp = 360
        demo_user.level = 2
        demo_user.streak = 5
        demo_user.last_active = now().date()
        demo_user.save()

        # Simulate Practice History logs for demouser for the past 7 days
        # This populates the Chart.js line graph instantly!
        self.stdout.write("Simulating practice session logs for charts...")
        today = now().date()
        
        # 7-day volume: Mon-Sun
        # We create various logs distributed across the past week
        for i in range(7):
            log_date = today - timedelta(days=i)
            # Spawn between 2 to 8 practice attempts per day
            attempts = random.randint(2, 8)
            for _ in range(attempts):
                shortcut = random.choice(created_shortcuts)
                is_correct = random.choices([True, False], weights=[80, 20])[0]
                accuracy = 100.0 if is_correct else float(random.randint(40, 80))
                resp_time = round(random.uniform(0.6, 2.8), 2)
                xp_earned = random.choice([10, 20, 30]) if is_correct else 2
                
                # Create session log manually setting the timestamp back
                ps = PracticeSession.objects.create(
                    user=demo_user,
                    shortcut=shortcut,
                    accuracy=accuracy,
                    response_time=resp_time,
                    is_correct=is_correct,
                    xp_earned=xp_earned
                )
                # Overwrite django auto_now_add for simulation date mapping
                ps.created_at = now() - timedelta(days=i)
                ps.save()

                # Also populate activity logs
                ActivityLog.objects.create(
                    user=demo_user,
                    activity_type='complete_practice',
                    shortcut=shortcut,
                    details=f"Simulated. Correct: {is_correct}. Acc: {accuracy}%",
                    timestamp=now() - timedelta(days=i)
                )

        # Unlock some achievements for demouser
        UserAchievement.objects.get_or_create(user=demo_user, achievement=achievements['first-step'])
        UserAchievement.objects.get_or_create(user=demo_user, achievement=achievements['perfectionist'])

        self.stdout.write(self.style.SUCCESS("Database seeded successfully! Ready for test-run."))
