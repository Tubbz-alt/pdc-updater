import mock

import pdcupdater.utils
from pdcupdater.tests.handler_tests import (
    BaseHandlerTest, mock_pdc
)


class TestBuildtimeDepIngestion(BaseHandlerTest):
    maxDiff = None
    handler_path = 'pdcupdater.handlers.depchain.rpms:NewRPMBuildTimeDepChainHandler'
    config = {}

    @mock.patch('pdcupdater.utils.rawhide_tag')
    @mock.patch('pdcupdater.handlers.depchain.rpms.interesting_tags')
    def test_can_handle_buildsys_tag_message(self, tags, rawhide):
        tags.return_value = ['f24']
        rawhide.return_value = 'f24'
        idx = '2016-662e75d1-5830-4c84-9855-fd07a3018f7a'
        msg = pdcupdater.utils.get_fedmsg(idx)
        result = self.handler.can_handle(msg)
        self.assertEquals(result, True)

    @mock_pdc
    @mock.patch('pdcupdater.utils.rawhide_tag')
    @mock.patch('pdcupdater.handlers.depchain.rpms.interesting_tags')
    def test_handle_new_build(self, pdc, tags, rawhide):
        tags.return_value = ['f24']
        rawhide.return_value = 'f24'

        idx = '2016-662e75d1-5830-4c84-9855-fd07a3018f7a'
        msg = pdcupdater.utils.get_fedmsg(idx)
        self.handler.handle(pdc, msg)
        expected_keys = [
            'release-component-relationships',
            'releases/fedora-24',
            'release-component-relationships/1',
            'release-components',
            'global-components',
        ]
        self.assertEquals(pdc.calls.keys(), expected_keys)

        self.assertEqual(len(pdc.calls['global-components']), 53116)
        self.assertEqual(len(pdc.calls['release-components']), 53116)
        self.assertEqual(len(pdc.calls['release-component-relationships']), 17709)

        self.assertEqual(
            pdc.calls['release-component-relationships/1'],
            [('DELETE', {}), ('DELETE', {})],
        )

    @mock_pdc
    @mock.patch('pdcupdater.utils.rawhide_tag')
    @mock.patch('pdcupdater.handlers.depchain.rpms.interesting_tags')
    @mock.patch('pdcupdater.services.koji_list_buildroot_for')
    @mock.patch('pdcupdater.services.koji_rpms_from_build')
    @mock.patch('pdcupdater.services.koji_builds_in_tag')
    def test_audit_empty_koji(self, pdc, builds, rpms, buildroot, tags, rawhide):
        tags.return_value = ['f24']
        rawhide.return_value = 'f24'

        # Mock out koji results
        builds.return_value = [{
            'build_id': 'fake_build_id',
            'name': 'guake',
        }]
        rpms.return_value = {}, []
        buildroot.return_value = 'wat2'

        # Call the auditor
        present, absent = self.handler.audit(pdc)

        # Check the PDC calls..
        self.assertDictEqual(pdc.calls, {
            'release-component-relationships': [
                ('GET', {
                    'page': 1,
                    'from_component_release': 'fedora-24',
                    'type': 'RPMBuildRequires',
                }),
                ('GET', {
                    'page': 1,
                    'from_component_release': 'fedora-24',
                    'type': 'RPMBuildRoot',
                }),
            ],
            'releases/fedora-24': [('GET', {})]
        })

        # Check the results.
        self.assertSetEqual(present, set())
        self.assertSetEqual(absent, set())

    @mock_pdc
    @mock.patch('pdcupdater.utils.rawhide_tag')
    @mock.patch('pdcupdater.handlers.depchain.rpms.interesting_tags')
    @mock.patch('pdcupdater.services.koji_list_buildroot_for')
    @mock.patch('pdcupdater.services.koji_rpms_from_build')
    @mock.patch('pdcupdater.services.koji_builds_in_tag')
    def test_audit_mismatch(self, pdc, builds, rpms, buildroot, tags, rawhide):
        tags.return_value = ['f24']
        rawhide.return_value = 'f24'

        # Mock out koji results
        _build = {
            'build_id': 'fake_build_id',
            'name': 'guake',
        }
        builds.return_value = [_build]
        rpms.return_value = _build, ['some rpm filename']
        buildroot.return_value = [
            { 'name': 'buildtimelib1', 'is_update': True, },
            { 'name': 'buildtimelib2', 'is_update': False, },
        ]

        # Call the auditor
        present, absent = self.handler.audit(pdc)

        # Check the PDC calls..
        self.assertDictEqual(pdc.calls, {
            'release-component-relationships': [
                ('GET', {
                    'page': 1,
                    'from_component_release': 'fedora-24',
                    'type': 'RPMBuildRequires',
                }),
                ('GET', {
                    'page': 1,
                    'from_component_release': 'fedora-24',
                    'type': 'RPMBuildRoot',
                }),
            ],
            'releases/fedora-24': [('GET', {})]
        })

        # Check the results.
        self.assertSetEqual(present, set([]))
        self.assertSetEqual(absent, set([
            'guake/fedora-24 RPMBuildRequires buildtimelib1/fedora-24',
            'guake/fedora-24 RPMBuildRoot buildtimelib2/fedora-24',
        ]))


class TestRuntimeDepIngestion(BaseHandlerTest):
    handler_path = 'pdcupdater.handlers.depchain.rpms:NewRPMRunTimeDepChainHandler'
    config = {}

    @mock_pdc
    @mock.patch('pdcupdater.utils.rawhide_tag')
    @mock.patch('pdcupdater.handlers.depchain.rpms.interesting_tags')
    @mock.patch('pdcupdater.services.koji_yield_rpm_requires')
    @mock.patch('pdcupdater.services.koji_rpms_from_build')
    @mock.patch('pdcupdater.services.koji_builds_in_tag')
    def test_audit_mismatch(self, pdc, builds, rpms, requires, tags, rawhide):
        tags.return_value = ['f24']
        rawhide.return_value = 'f24'

        # Mock out koji results
        _build = {
            'build_id': 'fake_build_id',
            'name': 'guake',
        }
        builds.return_value = [_build]
        rpms.return_value = _build, ['some rpm filename']
        requires.return_value = [
            ('runtimelib1', '', '',),
        ]

        # Call the auditor
        present, absent = self.handler.audit(pdc)

        # Check the PDC calls..
        self.assertDictEqual(pdc.calls, {
            'release-component-relationships': [ ('GET', {
                'page': 1, 'from_component_release': 'fedora-24', 'type': 'RPMRequires'
            })],
            'releases/fedora-24': [('GET', {})]
        })

        # Check the results.
        self.assertSetEqual(present, set(['guake/fedora-24 RPMRequires nethack/fedora-24']))
        self.assertSetEqual(absent, set(['guake/fedora-24 RPMRequires runtimelib1/fedora-24']))

    @mock_pdc
    @mock.patch('pdcupdater.utils.rawhide_tag')
    @mock.patch('pdcupdater.handlers.depchain.rpms.interesting_tags')
    @mock.patch('pdcupdater.services.koji_yield_rpm_requires')
    @mock.patch('pdcupdater.services.koji_rpms_from_build')
    @mock.patch('pdcupdater.services.koji_builds_in_tag')
    def test_audit_simple_match(self, pdc, builds, rpms, requires, tags, rawhide):
        tags.return_value = ['f24']
        rawhide.return_value = 'f24'

        # Mock out koji results
        _build = {
            'build_id': 'fake_build_id',
            'name': 'guake',
        }
        builds.return_value = [_build]
        rpms.return_value = _build, ['some rpm filename']
        requires.return_value = [
            ('nethack', '', '',),
        ]

        # Call the auditor
        present, absent = self.handler.audit(pdc)

        # Check the PDC calls..
        self.assertDictEqual(pdc.calls, {
            'release-component-relationships': [ ('GET', {
                'page': 1, 'from_component_release': 'fedora-24', 'type': 'RPMRequires'
            })],
            'releases/fedora-24': [('GET', {})]
        })

        # Check the results.
        self.assertSetEqual(present, set())
        self.assertSetEqual(absent, set())

    @mock_pdc
    @mock.patch('pdcupdater.utils.rawhide_tag')
    @mock.patch('pdcupdater.handlers.depchain.rpms.interesting_tags')
    @mock.patch('pdcupdater.services.koji_yield_rpm_requires')
    @mock.patch('pdcupdater.services.koji_rpms_from_build')
    @mock.patch('pdcupdater.services.koji_builds_in_tag')
    def test_initialize(self, pdc, builds, rpms, requires, tags, rawhide):
        tags.return_value = ['f24']
        rawhide.return_value = 'f24'

        # Mock out koji results
        _build = {
            'build_id': 'fake_build_id',
            'name': 'guake',
        }
        builds.return_value = [_build]
        rpms.return_value = _build, ['some rpm filename']
        requires.return_value = [
            ('nethack', '', '',),
        ]

        # Call the initializer
        self.handler.initialize(pdc)

        # Check the PDC calls..

        expected_calls = {
            'global-components': [
                ('GET', {'name': 'guake'}),
                ('GET', {'name': 'nethack'}),
                ('GET', {'name': 'guake'}),
                ('GET', {'name': 'nethack'})
            ],
            'release-component-relationships': [
                ('POST',
                 {'to_component': {'name': 'nethack',
                                   'release': {'release_id': 'fedora-24'}},
                  'from_component': {'name': 'guake',
                                     'release': {'release_id': 'fedora-24'}},
                  'type': 'RPMRequires'})],
            'release-components': [
                ('POST',
                 {'global_component': 'guake',
                  'name': 'guake',
                  'release': 'fedora-24',
                  'type': 'rpm'}),
                ('POST',
                 {'global_component': 'nethack',
                  'name': 'nethack',
                  'release': 'fedora-24',
                  'type': 'rpm'}),
                ('POST',
                 {'global_component': 'guake',
                  'name': 'guake',
                  'release': 'fedora-24',
                  'type': 'rpm'}),
                ('POST',
                 {'global_component': 'nethack',
                  'name': 'nethack',
                  'release': 'fedora-24',
                  'type': 'rpm'})],
            'releases/fedora-24': [('GET', {}), ('GET', {})]
        }

        self.assertDictEqual(pdc.calls, expected_calls)
