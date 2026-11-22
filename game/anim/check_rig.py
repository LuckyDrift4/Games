"""numeric sanity check: feet on the floor, hands reaching their targets, left hand on the racket"""
import sys, math
import r6, rig
from clips import CLIPS, ORDER

names = sys.argv[1].split(',') if len(sys.argv) > 1 else ORDER
for name in names:
    clip = CLIPS[name]
    worst = {}
    for t, mats, P in rig.bake(clip):
        W = rig.world(mats)
        foot = {}
        for part, key in (('Right Leg', 'rf'), ('Left Leg', 'lf')):
            y = rig.pos_of(r6.mul(W[part], r6.mat(p=(0, -1, 0))))[1]
            lift = P[key][2]
            err = y - (rig.FLOOR + lift)
            foot[key] = err
        hand = rig.pos_of(r6.mul(W['Right Arm'], r6.mat(p=r6.HAND)))
        eh = rig.length(rig.sub(hand, rig.C(P['rh'])))
        lhp = rig.pos_of(r6.mul(W['Left Arm'], r6.mat(p=(0, -1, 0))))
        g, s = P['grab']
        if g > 0.5:
            torso = W['Torso']
            sw = rig.grip_s(torso, W['Racket'], s)
            on = rig.racket_point(mats, sw)
            el = rig.length(rig.sub(lhp, on))
        else:
            el = 0
        for key, v in (('rf', foot['rf']), ('lf', foot['lf']), ('rh', eh), ('lh', el)):
            if abs(v) > abs(worst.get(key, (0, 0))[0]):
                worst[key] = (v, round(t, 2))
    print('%-15s' % name, '  '.join('%s %+.2f@%.2f' % (k_, v[0], v[1]) for k_, v in sorted(worst.items())))
