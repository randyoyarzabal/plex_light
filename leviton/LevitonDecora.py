from decora_wifi import DecoraWiFiSession
from decora_wifi.models.person import Person
from decora_wifi.models.residential_account import ResidentialAccount


class LevitonDecora:

    def __init__(self, **kwargs):
        self.residence = kwargs.get('decora_residence')
        try:
            self.session = DecoraWiFiSession()
            self.session.login(kwargs.get('decora_email'), kwargs.get('decora_pass'))
        except Exception:
            raise RuntimeError("Unable to login to MyLeviton Cloud. Check user/pass.")

    def get_switch(self, switch_name):
        for perm in self.session.user.get_residential_permissions():
            acct = ResidentialAccount(self.session, perm.residentialAccountId)
            for res in acct.get_residences():
                if res.name == self.residence:
                    for switch in res.get_iot_switches():
                        if switch.name == switch_name:
                            return switch

    def control_switch(self, name, power_state='OFF', brightness=0):
        power = power_state

        # Force power to 'ON' if brightness is set.
        if brightness > 0:
            power = 'ON'

        switch = self.get_switch(name)
        if switch:
            switch.update_attributes({'power': power, 'brightness': brightness})
            switch.refresh()
        else:
            raise RuntimeError(
                "Switch: '{}' not found. Verify name and/or residence is correct.".format(name))

    def list_names(self):
        """
        Given proper credentials, this is used for discovery of permissions, residences, switches, and activities.
        """
        perms = self.session.user.get_residential_permissions()
        for permission in perms:
            print("Permissions:")
            print('   ID: ' + str(permission.residentialAccountId))
            acct = ResidentialAccount(self.session, permission.residentialAccountId)
            for res in acct.get_residences():
                print("   Residences:")
                print('      ' + res.name)

                print("         Switches:")
                for switch in res.get_iot_switches():
                    print('            ' + switch.name)

                print("      Activities:")
                for act in res.get_residential_activities():
                    print('            ' + act.name)

    def run_activity(self, activity_name):
        activity_found = False
        perms = self.session.user.get_residential_permissions()
        for permission in perms:
            acct = ResidentialAccount(self.session, permission.residentialAccountId)
            for res in acct.get_residences():
                if res.name == self.residence:
                    for act in res.get_residential_activities():
                        if act.name == activity_name:
                            activity_found = True
                            act.execute(self.session, {'id': act.id})

        if not activity_found:
            raise RuntimeError(
                "Activity: '{}' not found. Verify name and/or residence is correct.".format(activity_name))

    def log_out(self):
        Person.logout(self.session)

    def __del__(self):
        # Clean-up just in case log_out wasn't called.
        try:
            Person.logout(self.session)
        except Exception:
            pass
