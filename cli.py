import os
import sys
import cmd
import glob
import re

from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

from kuj_orm import Base, Exp, Mtab, DomDb, default_config, etl
from complete_path import complete_path
from utils import asciitable

from test import get_psql_engine

DEBUG=False
# ORM session management
def get_session_factory():
    if DEBUG:
        engine = sqlalchemy.create_engine('sqlite://')
    else:
        #engine = get_sqlite_engine(delete=False)
        engine = get_psql_engine()
    Base.metadata.create_all(engine)
    Session = sessionmaker()
    Session.configure(bind=engine)
    return Session

def list_exps(session):
    # list experiments, and stats about them
    def q():
        # for all experiments
        for exp in session.query(Exp).all():
            n_samples = len(exp.samples) # count the samples
            # count the metabolites
            n_mtabs = session.query(func.count(Mtab.id)).filter(Mtab.exp==exp).first()[0]
            # return a row
            yield {
                'name': exp.name,
                'samples': n_samples,
                'metabolites': n_mtabs
            }
    # format the rows nicely
    for line in asciitable(list(q()),['name','samples','metabolites'],'Database is empty'):
        print line

def list_exp_files(dir):
    """lists all experiments. assumes filenames are in the format
    {exp_name}_{anything}.csv = data file
    {exp_name}_{anything including "metadata"}.csv = metadata file
    converts exp name to lowercase.
    returns basenames of files (without directory)"""
    result = {}
    for fn in glob.glob(os.path.join(dir,'*.csv')):
        bn = os.path.basename(fn)
        bnl = bn.lower()
        name = re.sub('_.*','',bnl)
        if name not in result:
            result[name] = {}
        if bnl.find('metadata') >= 0:
            result[name]['metadata'] = fn
        else:
            result[name]['data'] = fn 
    for exp,v in result.items():
        if 'data' in v and 'metadata' in v:
            yield {
                'name': exp,
                'data': os.path.basename(v['data']),
                'metadata': os.path.basename(v['metadata'])
                }

class Shell(cmd.Cmd):
    def __init__(self,session_factory):
        cmd.Cmd.__init__(self)
        self.prompt = 'domdb> '
        self.session_factory = session_factory
        self.config = default_config()
        self.do_count('')
    def do_count(self,args):
        with DomDb(self.session_factory, self.config) as domdb:
            if not args:
                n = domdb.mtab_count()
                print '%d metabolites in database' % n
            else:
                exp = args.split(' ')[0]
                n = domdb.mtab_count(exp)
                print '%d metabolites in experiment %s' % (n, exp)
    def do_list(self,args):
        session = self.session_factory()
        list_exps(session)
        session.close()
    def do_dir(self, args):
        dir = args
        result = list(list_exp_files(dir))
        print 'found files for %d experiments in %s' % (len(result), dir)
        for line in asciitable(result,disp_cols=['name','data','metadata']):
            print line
    def complete_dir(self, text, line, start_idx, end_idx):
        return complete_path(text, line)
    def do_add_dir(self, args):
        dir = args
        result = list(list_exp_files(dir))
        print 'found files for %d experiments in %s' % (len(result), dir)
        with DomDb(self.session_factory, self.config) as domdb:
            for d in result:
                name = d['name']
                path = os.path.join(dir,d['data'])
                mdpath = os.path.join(dir,d['metadata'])
                print 'loading experiment %s from:' % name
                print '- data file %s' % path
                print '- metadata file %s' % mdpath
                def console_log(x):
                    print x
                etl(domdb.session,name,path,mdpath,log=console_log)
                n = domdb.session.query(func.count(Mtab.id)).first()[0]
                print '%d metabolites in database' % n
    def complete_add_dir(self, text, line, start_idx, end_idx):
        return complete_path(text, line)
    def do_add(self,args):
        try:
            exp, path, mdpath = args.split(' ')
        except ValueError:
            print 'ERROR: add takes [exp name] [data file] [metadata file]'
            return
        if not os.path.exists(path):
            print 'data file %s does not exist' % path
            return
        if not os.path.exists(mdpath):
            print 'metadata file %s does not exist' % mdpath
            return
        print 'loading experiment %s from:' % exp
        print 'data file %s' % path
        print 'metadata file %s' % mdpath
        session = self.session_factory()
        etl(session,exp,path,mdpath,log=console_log)
        n = session.query(func.count(Mtab.id)).first()[0]
        print '%d metabolites in database' % n
        session.close()
    def complete_add(self, text, line, start_idx, end_idx):
        return complete_path(text, line)
    def do_remove(self,args):
        try:
            exp = args.split(' ')[0]
        except ValueError:
            print 'ERROR: remove takes [exp name]'
            return
        print 'Removing all %s data ...' % exp
        with DomDb(self.session_factory, self.config) as domdb:
            domdb.remove_exp(exp)
        self.do_list('')
    def do_exit(self,args):
        sys.exit(0)
    def do_quit(self,args):
        sys.exit(0)

if __name__=='__main__':
    shell = Shell(get_session_factory())
    shell.cmdloop('DOMDB v1')