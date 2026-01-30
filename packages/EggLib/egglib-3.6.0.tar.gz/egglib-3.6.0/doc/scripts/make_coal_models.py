import svgwrite


class model:
    def __init__(self, fname):
        self.fname = fname

    def __enter__(self):
        self.dwg = svgwrite.Drawing(self.fname, size=(1000, 1000))
        return self

    def __exit__(self, type, value, traceback):
        self.dwg.add(self.dwg.line(start=(150,10), end=(150,1000), stroke='black', stroke_width=8))
        self.dwg.add(self.dwg.polygon(points=[(150,0), (125,50), (175,50)], fill='black', stroke_width=0))
        self.dwg.save()

    def add_rect(self, fromx, tox, fromy, toy):
        fromy = 1000-fromy
        toy = 1000-toy
        self.dwg.add(self.dwg.rect(insert=(fromx, toy), size=(tox-fromx, fromy-toy), fill='gray'))

    def add_pop(self, midx, y, w, ln):
        y = 1000-y
        self.dwg.add(self.dwg.rect(insert=(midx-w/2.0, (y-ln)), size=(w, ln), fill='gray'))

    def add_ghost(self, midx, y, w, ln):
        y = 1000-y
        self.dwg.add(self.dwg.line(start=(midx-w/2.0,y), end=(midx-w/2.0,y-ln), stroke='gray', stroke_width=5, stroke_dasharray="5,5"))
        self.dwg.add(self.dwg.line(start=(midx+w/2.0,y), end=(midx+w/2.0,y-ln), stroke='gray', stroke_width=5, stroke_dasharray="5,5"))

    def add_date(self, y, t, stop, ext=None):
        y = 1000-y
        self.dwg.add(self.dwg.line(start=(150,y), end=(stop,y), stroke='black', stroke_width=3, stroke_dasharray="5,5"))
        if len(t) == 4: pos=20
        elif len(t) == 3: pos=50
        else: raise ValueError
        self.dwg.add(self.dwg.text(t, insert=(pos, y+15), font_family='sans', font_size=50, text_anchor='start'))
        if ext is not None:
            self.dwg.add(self.dwg.line(start=(ext[0],y), end=(ext[1],y), stroke='black', stroke_width=3, stroke_dasharray="5,5"))

    def add_text(self, x, y, t):
        y = 1000-y
        self.dwg.add(self.dwg.text(t, insert=(x, y+15), font_family='sans', font_size=50, text_anchor='middle', fill="black"))

    def add_line(self, fromx, tox, fromy, toy, dotted=False):
        fromy = 1000-fromy
        toy = 1000-toy
        if dotted:
            self.dwg.add(self.dwg.line(start=(fromx,fromy), end=(tox,toy), stroke='black', stroke_width=4, stroke_dasharray="5,5"))
        else:
            self.dwg.add(self.dwg.line(start=(fromx,fromy), end=(tox,toy), stroke='black', stroke_width=4))

    def add_2nd_scale(self, fromy, toy, text):
        fromy = 1000-fromy
        toy = 1000-toy
        self.dwg.add(self.dwg.line(start=(900,toy+10), end=(900,fromy), stroke='black', stroke_width=8))
        self.dwg.add(self.dwg.polygon(points=[(900,toy), (875,toy+50), (925,toy+50)], fill='black', stroke_width=0))
        self.dwg.add(self.dwg.text(text, insert=(920, (fromy-toy)/2.0+toy+30), font_family='sans', font_size=50, text_anchor='start'))

    def add_arrow(self, fromx, tox, y):
        y = 1000-y
        sign = -1 if tox>fromx else +1
        self.dwg.add(self.dwg.line(start=(fromx,y), end=(tox+sign*10,y), stroke='black', stroke_width=4, stroke_dasharray="5,5"))
        self.dwg.add(self.dwg.polygon(points=[(tox,y), (tox+sign*75,y+15), (tox+sign*75, y-15)], fill='black', stroke_width=0))

    def add_dearrow(self, fromx, tox, y):
        y = 1000-y
        self.dwg.add(self.dwg.line(start=(fromx+10,y), end=(tox-10,y), stroke='grey', stroke_width=8, stroke_dasharray="5,5"))
        self.dwg.add(self.dwg.polygon(points=[(tox,y), (tox-25,y+25), (tox-25, y-25)], fill='grey', stroke_width=0))
        self.dwg.add(self.dwg.polygon(points=[(fromx,y), (fromx+25,y+25), (fromx+25, y-25)], fill='grey', stroke_width=0))

    def add_sample(self, midx, w, text, weak, y=0):
        y = 1000-y
        if y == 1000: y-=30
        if weak:
            self.dwg.add(self.dwg.rect(insert=(midx-w/2.0, y-25), size=(w, 50), fill='none', stroke='black', stroke_width=5, stroke_dasharray="5,5"))
        else:
            self.dwg.add(self.dwg.rect(insert=(midx-w/2.0, y-25), size=(w, 50), fill='none', stroke='black', stroke_width=10))
        self.dwg.add(self.dwg.text(text, insert=(midx, y+15), font_family='sans', font_size=40, text_anchor='middle'))


with model('pict/model1.svg') as m:
    m.add_pop(midx=400, y=0, w=200, ln=1000)
    m.add_pop(midx=800, y=0, w=200, ln=450)
    m.add_pop(midx=600, y=450, w=600, ln=100) # fusion
    m.add_ghost(midx=800, y=550, w=200, ln=450)


with model('pict/model2.svg') as m:
    m.add_pop(midx=500, y=0, w=300, ln=450)
    m.add_pop(midx=500, y=450, w=100, ln=100)
    m.add_pop(midx=500, y=550, w=300, ln=650)
    m.add_date(y=450, t="0.20", stop=350)
    m.add_date(y=550, t="0.21", stop=350)
    m.add_text(x=500, y=500, t="0.1")

with model('pict/model3.svg') as m:
    m.add_pop(midx=500, y=0, w=300, ln=1000)
    m.add_line(fromx=350,tox=650,fromy=450,toy=450)
    m.add_line(fromx=650,tox=900,fromy=450,toy=300)
    m.add_line(fromx=650,tox=900,fromy=450,toy=600)
    m.add_date(y=450, t="0.20", stop=350)
    m.add_2nd_scale(fromy=300, toy=600, text='0.5')

with model('pict/model4.svg') as m:
    m.add_pop(midx=400, y=0, w=200, ln=1000)
    m.add_pop(midx=800, y=0, w=200, ln=1000)
    m.add_pop(midx=600, y=450, w=600, ln=100) # admixture
    m.add_arrow(fromx=400, tox=800, y=500)
    m.add_line(fromx=400,tox=400,fromy=300,toy=500, dotted=True)

with model('pict/model5.svg') as m:
    m.add_pop(midx=400, y=0, w=200, ln=1000)
    m.add_ghost(midx=800, y=0, w=200, ln=450)
    m.add_pop(midx=800, y=550, w=200, ln=450)
    m.add_pop(midx=600, y=450, w=600, ln=100) # admixture
    m.add_arrow(fromx=400, tox=800, y=500)
    m.add_line(fromx=400,tox=400,fromy=300,toy=500, dotted=True)

with model('pict/model6.svg') as m:
    m.add_pop(midx=400, y=0, w=200, ln=1000)
    m.add_pop(midx=800, y=0, w=200, ln=450)
    m.add_pop(midx=600, y=450, w=600, ln=100) # fusion
    m.add_ghost(midx=800, y=550, w=200, ln=450)
    m.add_arrow(fromx=800, tox=400, y=500)
    m.add_line(fromx=800,tox=800,fromy=300,toy=500, dotted=True)

with model('pict/model7.svg') as m:
    m.add_pop(midx=300, y=0, w=150, ln=1000)
    m.add_pop(midx=550, y=0, w=150, ln=1000)
    m.add_ghost(midx=800, y=0, w=150, ln=1000)
    m.add_dearrow(fromx=375, tox=475, y=200)
    m.add_dearrow(fromx=375, tox=475, y=400)
    m.add_dearrow(fromx=375, tox=475, y=600)
    m.add_dearrow(fromx=375, tox=475, y=800)
    m.add_sample(midx=300, w=150, text="n=20", weak=False)
    m.add_sample(midx=550, w=150, text="n=0", weak=True)
    m.add_sample(midx=800, w=150, text="n=0", weak=True)

with model('pict/model8.svg') as m:
    m.add_pop(midx=400, y=0, w=200, ln=1000)
    m.add_pop(midx=800, y=0, w=200, ln=1000)
    m.add_sample(midx=400, w=200, text="n=1", weak=False)
    m.add_sample(midx=800, w=200, text="n=1", weak=False)

with model('pict/model9.svg') as m:
    m.add_pop(midx=300, y=0, w=150, ln=1000)
    m.add_pop(midx=550, y=0, w=150, ln=1000)
    m.add_ghost(midx=800, y=0, w=150, ln=450)
    m.add_rect(fromx=475, tox=875, fromy=450, toy=550) # fusion
    m.add_pop(midx=800, y=550, w=150, ln=500)

    m.add_dearrow(fromx=375, tox=475, y=200)
    m.add_dearrow(fromx=375, tox=475, y=400)
    m.add_dearrow(fromx=375, tox=475, y=600)
    m.add_dearrow(fromx=375, tox=475, y=800)

    m.add_date(y=500, t="0.50", stop=225)

    m.add_sample(midx=300, w=150, text="n=20", weak=False)
    m.add_sample(midx=550, w=150, text="n=0", weak=True)
    m.add_sample(midx=800, w=150, text="n=0", weak=True)

with model('pict/model10.svg') as m:
    m.add_pop(midx=300, y=0, w=150, ln=750)
    m.add_pop(midx=550, y=0, w=150, ln=1000)
    m.add_ghost(midx=800, y=0, w=150, ln=350)

    m.add_rect(fromx=475, tox=875, fromy=350, toy=450) # fusion1
    m.add_pop(midx=800, y=450, w=150, ln=600)
    m.add_date(y=400, t="0.30", stop=225)

    m.add_rect(fromx=225, tox=625, fromy=650, toy=750) # fusion2
    m.add_ghost(midx=300, y=750, w=150, ln=250)
    m.add_date(y=700, t="0.50", stop=225)

    m.add_dearrow(fromx=375, tox=475, y=200)
    m.add_dearrow(fromx=375, tox=475, y=400)
    m.add_dearrow(fromx=375, tox=475, y=600)

    m.add_date(y=400, t="0.30", stop=225)

    m.add_sample(midx=300, w=150, text="n=20", weak=False)
    m.add_sample(midx=550, w=150, text="n=0", weak=True)
    m.add_sample(midx=800, w=150, text="n=0", weak=True)

with model('pict/model11.svg') as m:
    m.add_pop(midx=500, y=0, w=300, ln=1000)
    m.add_sample(midx=500, w=300, text="n=20", weak=False)
    m.add_sample(midx=500, w=300, y=500, text="n=20", weak=False)
    m.add_date(y=500, t="0.50", stop=350)

with model('pict/model12.svg') as m:
    m.add_pop(midx=400, y=0, w=200, ln=1000)
    m.add_ghost(midx=800, y=0, w=200, ln=300)
    m.add_pop(midx=800, y=275, w=200, ln=475)
    m.add_pop(midx=600, y=750, w=600, ln=100) # fusion
    m.add_ghost(midx=800, y=850, w=200, ln=150)
    m.add_arrow(fromx=800, tox=400, y=800)
    m.add_line(fromx=800,tox=800,fromy=600,toy=800, dotted=True)
    m.add_sample(midx=400, w=200, text="n=20", weak=False)
    m.add_sample(midx=800, w=200, y=300, text="n=20", weak=False)
    m.add_date(y=300, t="0.2", stop=300, ext=(500, 700))
    m.add_date(y=800, t="1.0", stop=300)

with model('pict/model13.svg') as m:
    m.add_pop(midx=300, y=0, w=150, ln=200)
    m.add_pop(midx=550, y=0, w=150, ln=1000)
    m.add_pop(midx=800, y=0, w=150, ln=800)
    m.add_sample(midx=300, w=150, text="n=2*4", weak=False)
    m.add_sample(midx=550, w=150, text="n=2*4", weak=False)
    m.add_sample(midx=800, w=150, text="n=2*1", weak=False)

    # fusion1
    m.add_rect(fromx=225, tox=625, fromy=200, toy=300)
    m.add_arrow(fromx=300, tox=550, y=250)
    m.add_line(fromx=300,tox=300,fromy=50,toy=250, dotted=True)
    m.add_ghost(midx=300, y=300, w=150, ln=700)
    m.add_date(y=250, t="0.5", stop=225)

    # fusion2
    m.add_rect(fromx=475, tox=875, fromy=800, toy=900)
    m.add_arrow(fromx=800, tox=550, y=850)
    m.add_line(fromx=800,tox=800,fromy=650,toy=850, dotted=True)
    m.add_ghost(midx=800, y=900, w=150, ln=100)
    m.add_date(y=850, t="3.0", stop=475)
