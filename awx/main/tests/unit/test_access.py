import pytest
import mock

from django.contrib.auth.models import User
from django.forms.models import model_to_dict

from awx.main.access import (
    BaseAccess,
    check_superuser,
    JobTemplateAccess,
)
from awx.main.models import Credential, Inventory, Project, Role, Organization


@pytest.fixture
def job_template_with_ids(job_template_factory):
    # Create non-persisted objects with IDs to send to job_template_factory
    credential = Credential(id=1, pk=1, name='testcred', kind='ssh')
    net_cred = Credential(id=2, pk=2, name='testnetcred', kind='net')
    cloud_cred = Credential(id=3, pk=3, name='testcloudcred', kind='aws')
    inv = Inventory(id=11, pk=11, name='testinv')
    proj = Project(id=14, pk=14, name='testproj')

    jt_objects = job_template_factory(
        'testJT', project=proj, inventory=inv, credential=credential,
        cloud_credential=cloud_cred, network_credential=net_cred,
        persisted=False)
    return jt_objects.job_template

@pytest.fixture
def user_unit():
    return User(username='rando', password='raginrando', email='rando@redhat.com')

def test_superuser(mocker):
    user = mocker.MagicMock(spec=User, id=1, is_superuser=True)
    access = BaseAccess(user)

    can_add = check_superuser(BaseAccess.can_add)
    assert can_add(access, None) is True

def test_not_superuser(mocker):
    user = mocker.MagicMock(spec=User, id=1, is_superuser=False)
    access = BaseAccess(user)

    can_add = check_superuser(BaseAccess.can_add)
    assert can_add(access, None) is False

def test_jt_existing_values_are_nonsensitive(job_template_with_ids, user_unit):
    """Assure that permission checks are not required if submitted data is
    identical to what the job template already has."""

    data = model_to_dict(job_template_with_ids)
    access = JobTemplateAccess(user_unit)

    assert access.changes_are_non_sensitive(job_template_with_ids, data)

def test_change_jt_sensitive_data(job_template_with_ids, mocker, user_unit):
    """Assure that can_add is called with all ForeignKeys."""

    job_template_with_ids.admin_role = Role()

    data = {'inventory': job_template_with_ids.inventory.id + 1}
    access = JobTemplateAccess(user_unit)

    mock_add = mock.MagicMock(return_value=False)
    with mock.patch('awx.main.models.rbac.Role.__contains__', return_value=True):
        with mocker.patch('awx.main.access.JobTemplateAccess.can_add', mock_add):
            with mocker.patch('awx.main.access.JobTemplateAccess.can_read', return_value=True):
                assert not access.can_change(job_template_with_ids, data)

    mock_add.assert_called_once_with({
        'inventory': data['inventory'],
        'project': job_template_with_ids.project.id,
        'credential': job_template_with_ids.credential.id,
        'cloud_credential': job_template_with_ids.cloud_credential.id,
        'network_credential': job_template_with_ids.network_credential.id
    })

def test_jt_add_scan_job_check(job_template_with_ids, user_unit):
    "Assure that permissions to add scan jobs work correctly"

    access = JobTemplateAccess(user_unit)
    project = job_template_with_ids.project
    inventory = job_template_with_ids.inventory
    project.use_role = Role()
    inventory.use_role = Role()
    organization = Organization(name='test-org')
    inventory.organization = organization
    organization.admin_role = Role()

    def mock_get_object(Class, **kwargs):
        if Class == Project:
            return project
        elif Class == Inventory:
            return inventory
        else:
            raise Exception('Item requested has not been mocked')

    with mock.patch.object(JobTemplateAccess, 'check_license', return_value=None):
        with mock.patch('awx.main.models.rbac.Role.__contains__', return_value=True):
            with mock.patch('awx.main.access.get_object_or_400', mock_get_object):
                assert access.can_add({
                    'project': project.pk,
                    'inventory': inventory.pk,
                    'job_type': 'scan'
                })

def test_jt_can_add_bad_data(user_unit):
    "Assure that no server errors are returned if we call JT can_add with bad data"
    access = JobTemplateAccess(user_unit)
    assert not access.can_add({'asdf': 'asdf'})

