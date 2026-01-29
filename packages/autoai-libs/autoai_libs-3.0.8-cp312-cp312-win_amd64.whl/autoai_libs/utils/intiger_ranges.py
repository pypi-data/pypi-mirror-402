################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2021-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
def uniform_integers(rmin, rmax, size):
    """This method returns an integer array of roughly evenly spaced integers including rmin and rmax.
    The array size is approximately 'size'.  It may be smaller (e.g. if 1 + rmax + rmin < size ),
    a bit smaller if the step size calculated is slightly too large, or slightly larger if the step size calculated
    is slightly too small"""
    step = round((2 + rmax - rmin) / size)
    if step == 0:
        step = 1
    irange = []
    irange.extend(range(rmin, rmax + 1, step))
    if irange[-1] != rmax:
        irange.append(rmax)
    return irange
