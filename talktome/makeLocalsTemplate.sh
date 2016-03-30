#!/bin/bash
cat locals.cfg |sed 's/=.*$/=/g' > locals.cfg.template
