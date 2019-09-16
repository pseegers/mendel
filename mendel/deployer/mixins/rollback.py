from functools import partial

from mendel.util.colors import green


class SymlinkRollbackMixin(object):
    """
    Common behavior for deployers that use symlink rollback
    Must be mixedin to a subclass of Deployer as it relies on its methods
    """

    def symlink_rollback(self, connection):
        """
        Rollback by switching symlinks. Allow user choice for which version to roll back to
        :param connection: Connection
        :return: nothing
        """
        def validator(rollback_candidate, release_list):
            if rollback_candidate == self._get_current_release(connection):
                raise Exception(
                    'can\'t rollback to same version that is already deployed')

            if rollback_candidate not in release_list:
                raise Exception(
                    'invalid rollback selection: %s' % rollback_candidate)

            return rollback_candidate

        all_releases = self._get_all_releases(connection)
        if len(all_releases) <= 1:
            self._log_error_and_exit(connection, 'Only 1 release available, nothing to rollback to :(')

        curr_index = self._display_releases_for_rollback_selection(
            all_releases,
            self._get_current_release(connection)
        )

        # TODO use this?
        default_rollback_choice = all_releases[max(curr_index - 1, 0)]
        is_valid = partial(validator, release_list=all_releases)

        rollback_to = input('Rollback to:')
        try:
            is_valid(rollback_to)
        except Exception as e:
            self._log_error_and_exit(connection, str(e))

        self._change_symlink_to(connection, self._rpath('releases', rollback_to))
        self._start_or_restart(connection)
        print(green(f'successfully rolled back {self.config.service_name} to {rollback_to}'))

        self._track_event(connection, 'rolledback')

    def _get_all_releases(self, connection):
        """
        Get contents of the remote releases directory
        :param connection: Connection
        :return: list of release name strings
        """
        result = connection.sudo('ls -1 %s' % self._rpath('releases'),
                                 user=self.config.user)  # note: had to take out group=self.config.group
        releases = sorted([_.strip() for _ in result.stdout.split('\n') if _.strip() != ''])
        return releases

    @staticmethod
    def _display_releases_for_rollback_selection(releases, current):
        """
        display releases with current release flagged, also returns index of
        current release in release list
        Doesn't do anything on the remote host, just does manipulation for shell display
        :param: releases list of str releases (obtained from _get_all_releases)
        :param: current str current release
        :return: int index of where the current release is with respect to all releases
        """
        r_list, curr_index = [], None
        for i, r in enumerate(releases):
            if r == current:
                r_list.append(r + ' <-- current')
                curr_index = i
            else:
                r_list.append(r)

        for r in r_list:
            print(r)

        return curr_index
