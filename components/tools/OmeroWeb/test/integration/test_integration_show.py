#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
   Simple integration tests for the "show" module.

   Copyright 2014 Glencoe Software, Inc. All rights reserved.
   Use is subject to license terms supplied in LICENSE.txt

"""

import omero
import omero.clients
import pytest
import test.integration.library as lib

from omero.gateway import BlitzGateway, ProjectWrapper, DatasetWrapper, \
                          ImageWrapper
from omero.model import ProjectI, DatasetI, ImageI, TagAnnotationI
from omero.rtypes import rstring
from omeroweb.webclient.show import Show
from django.test.client import RequestFactory


@pytest.fixture(scope='module')
def path():
    return '/webclient'


@pytest.fixture(scope='module')
def request_factory():
    """Returns a fresh Django request factory."""
    return RequestFactory()


@pytest.fixture(scope='function')
def itest(request):
    o = lib.ITest()
    o.setup_method(None)

    def finalizer():
        o.teardown_method(None)
    request.addfinalizer(finalizer)
    return o


@pytest.fixture(scope='function')
def client(request, itest):
    return itest.new_client()


@pytest.fixture(scope='function')
def conn(request, client):
    return BlitzGateway(client_obj=client)


@pytest.fixture(scope='function')
def update_service(request, client):
    return client.getSession().getUpdateService()


@pytest.fixture(scope='function')
def project(request, itest, update_service):
    project = ProjectI()
    project.name = rstring(itest.uuid())
    return update_service.saveAndReturnObject(project)


@pytest.fixture(scope='function')
def project_dataset(request, itest, update_service):
    project = ProjectI()
    project.name = rstring(itest.uuid())
    dataset = DatasetI()
    dataset.name = rstring(itest.uuid())
    project.linkDataset(dataset)
    return update_service.saveAndReturnObject(project)


@pytest.fixture(scope='function')
def project_dataset_image(request, itest, update_service):
    project = ProjectI()
    project.name = rstring(itest.uuid())
    dataset = DatasetI()
    dataset.name = rstring(itest.uuid())
    image = itest.new_image(name=itest.uuid())
    dataset.linkImage(image)
    project.linkDataset(dataset)
    return update_service.saveAndReturnObject(project)


@pytest.fixture(scope='function')
def tag(request, itest, update_service):
    tag = TagAnnotationI()
    tag.textValue = rstring(itest.uuid())
    return update_service.saveAndReturnObject(tag)


@pytest.fixture(scope='function')
def project_path_request(request, project, request_factory, path):
    """
    Returns a simple GET request object with the 'path' query string
    variable set in the legacy ("project=id") form.
    """
    as_string = 'project=%d' % project.id.val
    initially_select = ['project-%d' % project.id.val]
    return {
        'request': request_factory.get(path, data={'path': as_string}),
        'initially_select': initially_select,
        'initially_open': initially_select
    }


@pytest.fixture(scope='function')
def project_dataset_path_request(
        request, project_dataset, request_factory, path):
    """
    Returns a simple GET request object with the 'path' query string
    variable set in the legacy ("project=id|dataset=id") form.
    """
    dataset, = project_dataset.linkedDatasetList()
    as_string = 'project=%d|dataset=%d' % \
        (project_dataset.id.val, dataset.id.val)
    initially_select = ['dataset-%d' % dataset.id.val]
    initially_open = [
        'project-%d' % project_dataset.id.val,
        'dataset-%d' % dataset.id.val
    ]
    return {
        'request': request_factory.get(path, data={'path': as_string}),
        'initially_select': initially_select,
        'initially_open': initially_open
    }


@pytest.fixture(scope='function')
def project_dataset_image_path_request(
        request, project_dataset_image, request_factory, path):
    """
    Returns a simple GET request object with the 'path' query string
    variable set in the legacy ("project=id|dataset=id|image=id") form.
    """
    dataset, = project_dataset_image.linkedDatasetList()
    image, = dataset.linkedImageList()
    as_string = 'project=%d|dataset=%d|image=%d' % \
        (project_dataset_image.id.val, dataset.id.val, image.id.val)
    initially_select = ['image-%d' % image.id.val]
    initially_open = [
        'project-%d' % project_dataset_image.id.val,
        'dataset-%d' % dataset.id.val,
        'image-%d' % image.id.val
    ]
    return {
        'request': request_factory.get(path, data={'path': as_string}),
        'initially_select': initially_select,
        'initially_open': initially_open
    }


@pytest.fixture(scope='function')
def tag_path_request_wrong_menu(
        request, tag, request_factory, path):
    """
    Returns a simple GET request object with the 'path' query string
    variable set in the legacy ("tag=id") form with the wrong (not 'usertags')
    menu.
    """
    as_string = 'tag=%d' % tag.id.val
    initially_select = ['tag-%d' % tag.id.val]
    initially_open = ['tag-%d' % tag.id.val]
    data = {'path': as_string, 'menu': 'userdata'}
    return {
        'request': request_factory.get(path, data=data),
        'initially_select': initially_select,
        'initially_open': initially_open
    }

class TestIntegrationShow(object):
    """
    Tests to ensure that OMERO.web "show" infrastructure is working
    correctly.
    """

    def assert_instantiation(self, show, request, conn):
        assert show.conn == conn
        assert show.initially_open is None
        assert show.initially_open_owner is None
        assert show.initially_select == request['initially_select']
        assert show.first_sel is None

    def test_project_legacy_path(self, conn, project_path_request, project):
        show = Show(conn, project_path_request['request'], None)
        self.assert_instantiation(show, project_path_request, conn)

        first_selected = show.get_first_selected()
        assert first_selected is not None
        assert isinstance(first_selected, ProjectWrapper)
        assert first_selected.getId() == project.id.val
        assert show.initially_open == project_path_request['initially_open']
        assert show.initially_open_owner == project.details.owner.id.val
        assert show.first_sel is None

    def test_project_dataset_legacy_path(
            self, conn, project_dataset_path_request, project_dataset):
        show = Show(conn, project_dataset_path_request['request'], None)
        self.assert_instantiation(show, project_dataset_path_request, conn)

        dataset, = project_dataset.linkedDatasetList()
        first_selected = show.get_first_selected()
        assert first_selected is not None
        assert isinstance(first_selected, DatasetWrapper)
        assert first_selected.getId() == dataset.id.val
        assert show.initially_open == \
            project_dataset_path_request['initially_open']
        assert show.initially_open_owner == project_dataset.details.owner.id.val
        assert show.first_sel is None

    def test_project_dataset_image_legacy_path(
            self, conn, project_dataset_image_path_request,
            project_dataset_image):
        show = Show(conn, project_dataset_image_path_request['request'], None)
        self.assert_instantiation(
            show, project_dataset_image_path_request, conn
        )

        dataset, = project_dataset_image.linkedDatasetList()
        image, = dataset.linkedImageList()
        first_selected = show.get_first_selected()
        assert first_selected is not None
        assert isinstance(first_selected, ImageWrapper)
        assert first_selected.getId() == image.id.val
        assert show.initially_open == \
            project_dataset_image_path_request['initially_open']
        assert show.initially_open_owner == \
            project_dataset_image.details.owner.id.val
        assert show.first_sel is None

    def test_tag_redirect(self, tag_path_request_wrong_menu):
        show = Show(conn, tag_path_request_wrong_menu['request'], None)
        self.assert_instantiation(
            show, tag_path_request_wrong_menu, conn
        )

        show.get_first_selected()